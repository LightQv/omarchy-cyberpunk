"""Exercise source drift detection and stable-release monitoring without a desktop."""

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compatibility

spec = importlib.util.spec_from_file_location("watch_omarchy", ROOT / "scripts/watch-omarchy-release.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class CompatibilityTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "shell/plugins/lock/Service.qml"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"reviewed authentication source\n")
        self.baseline = {
            "schemaVersion": 1, "packageVersion": "4.0.4-1", "tag": "v4.0.4",
            "repository": "omacom/omarchy", "commit": "a" * 40,
            "copies": {"shell/plugins/lock/Service.qml": "lock-plugin/Service.qml"},
            "files": {"shell/plugins/lock/Service.qml": hashlib.sha256(self.source.read_bytes()).hexdigest()},
        }

    def test_matching_audit_is_read_only(self):
        before = self.source.read_bytes()
        report = compatibility.audit(self.baseline, self.root, "4.0.4-1")
        self.assertTrue(report["compatible"])
        self.assertEqual(report["changes"], [])
        self.assertEqual(before, self.source.read_bytes())

    def test_package_revision_mismatch_requires_review_even_with_matching_files(self):
        report = compatibility.audit(self.baseline, self.root, "4.0.4-2")
        self.assertFalse(report["compatible"])
        self.assertEqual(report["changes"], [])

    def test_changed_lock_source_detected_without_preferences_or_activation(self):
        self.source.write_bytes(b"new upstream authentication flow\n")
        report = compatibility.audit(self.baseline, self.root, "4.0.4-1")
        self.assertFalse(report["compatible"])
        self.assertEqual(report["changes"][0]["status"], "changed")

    def test_missing_source_is_not_certified(self):
        self.source.unlink()
        report = compatibility.audit(self.baseline, self.root, "4.0.4-1")
        self.assertFalse(report["compatible"])
        self.assertEqual(report["changes"][0]["status"], "unavailable")

    def test_baseline_rejects_traversal_and_untracked_copies(self):
        path = self.root / "baseline.json"
        for mutation in ({"files": {"../outside": "a" * 64}}, {"copies": {"untracked": "clone"}}):
            path.write_text(json.dumps(dict(self.baseline, **mutation)))
            with self.assertRaises(ValueError):
                compatibility.load_baseline(path)

    def test_offline_cli_does_not_query_upstream_and_reports_json(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["compatibility.py", "--json", "--omarchy-root", str(self.root)]), \
                patch.object(compatibility, "load_baseline", return_value=self.baseline), \
                patch.object(compatibility.subprocess, "check_output", return_value="4.0.4-1\n"), \
                patch.object(compatibility, "latest_release") as network, redirect_stdout(output):
            self.assertEqual(compatibility.main(), 0)
        network.assert_not_called()
        self.assertTrue(json.loads(output.getvalue())["compatible"])

    def test_network_failure_is_not_reported_as_current(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["compatibility.py", "--upstream", "--json"]), \
                patch.object(compatibility, "load_baseline", return_value=self.baseline), \
                patch.object(compatibility.subprocess, "check_output", return_value="4.0.4-1\n"), \
                patch.object(compatibility, "latest_release", side_effect=OSError("API unavailable")), \
                redirect_stdout(output):
            self.assertEqual(compatibility.main(), 2)
        self.assertFalse(json.loads(output.getvalue())["compatible"])
        self.assertIn("API unavailable", json.loads(output.getvalue())["error"])

    def test_new_stable_release_needs_review_even_when_installed_sources_match(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["compatibility.py", "--upstream", "--json", "--omarchy-root", str(self.root)]), \
                patch.object(compatibility, "load_baseline", return_value=self.baseline), \
                patch.object(compatibility.subprocess, "check_output", return_value="4.0.4-1\n"), \
                patch.object(compatibility, "latest_release", return_value={"tag_name": "v4.0.5"}), \
                redirect_stdout(output):
            self.assertEqual(compatibility.main(), 1)
        report = json.loads(output.getvalue())
        self.assertTrue(report["compatible"])
        self.assertTrue(report["reviewRequired"])

    def test_repo_baseline_maps_existing_clones_and_lock_pins(self):
        baseline = compatibility.load_baseline()
        for destination in baseline["copies"].values():
            self.assertTrue((ROOT / destination).is_file(), destination)
        self.assertEqual(len(baseline["copies"]), 14)

    def test_monitor_ignores_current_and_older_stable_releases(self):
        with patch.object(watch, "gh") as gh:
            for tag in ("v4.0.4", "v4.0.3"):
                message = watch.monitor(self.baseline, {"tag_name": tag}, "owner/repo", create=True)
                self.assertIn("no issue needed", message)
        gh.assert_not_called()

    def test_monitor_uses_numeric_version_order_and_defaults_to_dry_run(self):
        with patch.object(watch, "gh") as gh:
            message = watch.monitor(self.baseline, {"tag_name": "v4.0.10"}, "owner/repo")
        self.assertIn("Would open: Omarchy v4.0.10 compatibility review", message)
        gh.assert_not_called()

    def test_monitor_does_not_reopen_existing_closed_review(self):
        issue = {"title": "Omarchy v4.0.5 compatibility review", "url": "https://github.com/owner/repo/issues/1"}
        with patch.object(watch, "gh", return_value=json.dumps([issue])) as gh:
            message = watch.monitor(self.baseline, {"tag_name": "v4.0.5"}, "owner/repo", create=True)
        self.assertIn(issue["url"], message)
        self.assertEqual(gh.call_count, 1)
        self.assertIn("all", gh.call_args.args)

    def test_monitor_creates_review_with_acceptance_and_upstream_diff(self):
        with patch.object(watch, "gh", side_effect=["[]", "https://github.com/owner/repo/issues/2"]) as gh:
            message = watch.monitor(self.baseline, {"tag_name": "v4.1.0"}, "owner/repo", create=True)
        self.assertIn("issues/2", message)
        creation = gh.call_args.args
        self.assertEqual(creation[:2], ("issue", "create"))
        body = creation[-1]
        self.assertIn("lock/unlock", body)
        self.assertIn(f"compare/{self.baseline['commit']}...v4.1.0", body)

    def test_monitor_rejects_prereleases_and_malformed_tags(self):
        for release in ({"tag_name": "v4.1.0", "prerelease": True}, {"tag_name": "v4.1.0-rc1"}):
            with self.assertRaises(ValueError):
                watch.monitor(self.baseline, release, "owner/repo", create=True)
