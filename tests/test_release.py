"""Exercise managed release transactions against the isolated native API simulator."""

import hashlib
import fcntl
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import unittest

import test_lifecycle


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_lifecycle.LifecycleTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.env = dict(self.fixture.env, XDG_DATA_HOME=str(self.fixture.home / ".local/share"))
        self.dest = self.fixture.home / ".local/share/omarchy-cyberpunk"
        self.state = self.fixture.home / ".local/state/omarchy-cyberpunk"
        self.payload = self.make_payload("v0.1.0")

    def make_payload(self, version):
        target = self.fixture.project.parent / version
        shutil.copytree(self.fixture.project, target, ignore=shutil.ignore_patterns(".state"))
        for name in ("install", "install.sh"):
            shutil.copyfile(test_lifecycle.ROOT / name, target / name)
        files = {str(path.relative_to(target)): {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": path.stat().st_mode & 0o777}
            for path in target.rglob("*") if path.is_file()}
        (target / "release.json").write_text(json.dumps({"version": version, "omarchy": "4.0.4-1", "files": files}))
        return target

    def run_release(self, payload=None, success=True, options=()):
        payload = payload or self.payload
        result = subprocess.run(["python", "-B", str(payload / "scripts/release.py"), "install", str(payload), *options],
                                env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def cli(self, *args, success=True):
        result = subprocess.run([str(self.fixture.home / ".local/bin/cyberpunk"), *args],
                                env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_fresh_layout_survives_deleted_download_and_uninstalls(self):
        self.run_release()
        for name in ("theme", "menu-plugin", "lock-plugin"):
            self.assertTrue((self.dest / name).is_symlink())
            self.assertFalse((self.dest / name).resolve().is_symlink())
        self.assertFalse((self.fixture.home / ".config/omarchy/themes/cyberpunk").is_symlink())
        self.assertTrue((self.state / "safe-mode").exists())
        shutil.rmtree(self.payload)
        self.assertIn("v0.1.0", self.cli("version").stdout)
        self.cli("enable", "all")
        self.cli("check")
        self.cli("uninstall")
        self.assertFalse(self.dest.exists())
        self.assertTrue((self.state / "preferences.json").exists())
        self.assertEqual(json.loads(self.fixture.config.read_text()), self.fixture.original)

    def test_repeat_install_and_upgrade_preserve_mixed_preferences(self):
        self.run_release()
        self.cli("enable", "menu")
        preferences = (self.state / "preferences.json").read_bytes()
        self.run_release()
        newer = self.make_payload("v0.1.1")
        self.run_release(newer)
        self.assertIn("v0.1.1", self.cli("version").stdout)
        self.assertEqual((self.state / "preferences.json").read_bytes(), preferences)
        self.cli("check")

    def test_checkout_migration_preserves_choices_and_stock_lock(self):
        self.fixture.run_script("install-dev")
        self.fixture.run_script("cyberpunk", "enable", "all")
        preferences = (self.state / "preferences.json").read_bytes()
        self.run_release()
        self.assertEqual((self.state / "preferences.json").read_bytes(), preferences)
        self.assertIn("safe mode", self.cli("status").stdout)
        self.assertTrue(self.fixture.project.exists())
        self.cli("uninstall")

    def test_edited_native_and_support_files_are_protected(self):
        self.run_release()
        palette = self.fixture.home / ".config/omarchy/themes/cyberpunk/colors.toml"
        original = palette.read_bytes()
        palette.write_bytes(original + b"\n# personal change\n")
        newer = self.make_payload("v0.1.1")
        self.run_release(newer, success=False)
        self.cli("uninstall", success=False)
        self.assertTrue(palette.read_bytes().endswith(b"# personal change\n"))
        palette.write_bytes(original)
        script = self.dest / "scripts/common.sh"
        script.write_text(script.read_text() + "\n# personal change\n")
        self.run_release(newer, success=False)
        self.assertTrue(self.dest.exists())

    def test_failed_update_restores_previous_release(self):
        self.run_release()
        self.cli("enable", "menu")
        self.fixture.control.write_text(json.dumps({"fail_once": "theme set cyberpunk"}))
        self.run_release(self.make_payload("v0.1.1"), success=False)
        self.assertIn("v0.1.0", self.cli("version").stdout)
        self.cli("check")
        self.assertFalse((self.state / "release-transaction").exists())

    def test_bad_manifest_and_foreign_paths_fail_before_install(self):
        (self.payload / "scripts/common.sh").write_text("changed")
        self.run_release(success=False)
        self.assertFalse(self.dest.exists())
        self.assertEqual(json.loads(self.fixture.config.read_text()), self.fixture.original)

    def test_foreign_cli_is_not_replaced(self):
        cli = self.fixture.home / ".local/bin/cyberpunk"
        cli.parent.mkdir(parents=True)
        cli.write_text("user-owned command")
        self.run_release(success=False)
        self.assertEqual(cli.read_text(), "user-owned command")
        self.assertFalse(self.dest.exists())

    def test_failed_recovery_is_resumable(self):
        self.run_release()
        newer = self.make_payload("v0.1.1")
        self.fixture.control.write_text('{"fail": "theme set cyberpunk"}')
        self.run_release(newer, success=False)
        self.assertTrue((self.state / "release-transaction/journal.json").exists())
        self.fixture.control.write_text("{}")
        self.run_release(newer)
        self.cli("check")
        self.assertIn("v0.1.1", self.cli("version").stdout)
        self.assertFalse((self.state / "release-transaction").exists())

    def test_locked_session_does_not_change_desktop(self):
        self.fixture.control.write_text('{"locked": true}')
        self.run_release(success=False)
        self.assertFalse(self.dest.exists())
        self.assertEqual(json.loads(self.fixture.config.read_text()), self.fixture.original)

    def test_release_operations_serialize_with_component_commands(self):
        lock = Path(self.env['XDG_RUNTIME_DIR']) / 'lightqv-cyberpunk-lifecycle.lock.operation'
        with lock.open('w') as descriptor:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self.run_release(success=False)
        self.assertFalse(self.dest.exists())

    def test_incomplete_snapshot_preparation_is_discarded(self):
        transaction = self.state / 'release-transaction'
        transaction.mkdir(parents=True, mode=0o700)
        (transaction / 'incomplete-snapshot').write_text('not committed')
        self.run_release()
        self.cli('check')
        self.assertFalse(transaction.exists())

    def test_same_version_cannot_replace_different_release_files(self):
        self.run_release()
        changed = self.fixture.project.parent / 'changed release'
        shutil.copytree(self.payload, changed)
        script = changed / 'scripts/common.sh'
        script.write_text(script.read_text() + '\n# changed release\n')
        manifest = json.loads((changed / 'release.json').read_text())
        manifest['files']['scripts/common.sh']['sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        (changed / 'release.json').write_text(json.dumps(manifest))
        self.run_release(changed, success=False)
        self.cli('check')

    def test_full_first_install_selects_all_once_but_keeps_stock_lock(self):
        result = self.run_release(options=('--setup', 'full', '--non-interactive'))
        self.assertTrue(all(json.loads((self.state / 'preferences.json').read_text())['components'].values()))
        self.assertIn('safe mode', result.stdout)
        self.cli('check')

    def test_asynchronous_discovery_finishes_before_activation(self):
        self.fixture.control.write_text('{"discovery_delay": 3}')
        self.run_release(options=('--setup', 'full', '--non-interactive'))
        self.assertEqual(json.loads(self.fixture.control.read_text())['discovery_delay'], 0)
        self.cli('check')

    def test_discovery_timeout_rolls_back_without_activating_components(self):
        self.fixture.control.write_text('{"discovery_delay": 100}')
        self.run_release(success=False, options=('--setup', 'full', '--non-interactive'))
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.state / 'preferences.json').exists())
        self.assertEqual(json.loads(self.fixture.config.read_text()), self.fixture.original)

    def test_unattended_custom_first_install(self):
        self.run_release(options=('--components', 'menu,osd,sudo', '--non-interactive'))
        values = json.loads((self.state / 'preferences.json').read_text())['components']
        self.assertEqual({name for name, enabled in values.items() if enabled}, {'menu', 'osd', 'sudo'})
        self.cli('check')

    def test_update_refuses_setup_override_and_preserves_preferences(self):
        self.run_release()
        self.cli('enable', 'menu')
        before = (self.state / 'preferences.json').read_bytes()
        self.run_release(self.make_payload('v0.1.1'), success=False, options=('--setup', 'full'))
        self.assertEqual((self.state / 'preferences.json').read_bytes(), before)
        self.cli('check')

    def test_retained_preferences_skip_first_install_selection(self):
        self.run_release()
        self.cli('enable', 'menu')
        before = (self.state / 'preferences.json').read_bytes()
        self.cli('uninstall')
        result = self.run_release()
        self.assertNotIn('Requested setup:', result.stdout)
        self.assertEqual((self.state / 'preferences.json').read_bytes(), before)

    def test_failed_first_install_restores_prior_preference_state(self):
        self.fixture.control.write_text('{"fail_once": "theme set cyberpunk"}')
        self.run_release(success=False, options=('--setup', 'full', '--non-interactive'))
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.state / 'preferences.json').exists())
        self.assertEqual(json.loads(self.fixture.config.read_text()), self.fixture.original)

    def test_invalid_or_unattended_interactive_choices_do_not_install(self):
        self.run_release(success=False, options=('--components', 'menu,unknown'))
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.state / 'preferences.json').exists())
        self.run_release(success=False, options=('--setup', 'custom', '--non-interactive'))
        self.assertFalse(self.dest.exists())

    def bootstrap(self, unsafe=False, mismatch=False, piped=False):
        download = self.fixture.home / "downloads"
        download.mkdir()
        temporary = self.fixture.home / "temporary"
        temporary.mkdir()
        name = "omarchy-cyberpunk-v0.1.0"
        asset = download / (name + ".tar.gz")
        with tarfile.open(asset, "w:gz") as archive:
            script = b'#!/bin/bash\nprintf installed > "$HOME/bootstrap-installed"\nprintf "%s\\n" "$@" > "$HOME/bootstrap-options"\n'
            entry = tarfile.TarInfo(("../escape" if unsafe else name + "/install"))
            entry.size = len(script)
            entry.mode = 0o755
            archive.addfile(entry, io.BytesIO(script))
        digest = "0" * 64 if mismatch else hashlib.sha256(asset.read_bytes()).hexdigest()
        (download / "SHA256SUMS").write_text(digest + "  " + asset.name + "\n")
        curl = Path(self.env["PATH"].split(":")[0]) / "curl"
        curl.write_text('''#!/usr/bin/python
import os,pathlib,shutil,sys
args=sys.argv[1:]
if "-o" not in args: print('{"tag_name":"v0.1.0"}')
else:
    url=next(arg for arg in args if arg.startswith("https://"))
    shutil.copyfile(pathlib.Path(os.environ["TEST_DOWNLOADS"])/url.rsplit("/",1)[1], args[args.index("-o")+1])
''')
        curl.chmod(0o755)
        command = ["bash", "-s", "--", "--setup", "full", "--non-interactive"] if piped else ["bash", str(test_lifecycle.ROOT / "install.sh")]
        script = (test_lifecycle.ROOT / "install.sh").read_text() if piped else None
        result = subprocess.run(command, input=script,
            env=dict(self.env, TEST_DOWNLOADS=str(download), TMPDIR=str(temporary)), capture_output=True, text=True, timeout=20)
        self.assertEqual(list(temporary.iterdir()), [], result.stdout + result.stderr)
        self.assertEqual((self.fixture.home / "bootstrap-installed").exists(), not (unsafe or mismatch))
        self.assertEqual(result.returncode == 0, not (unsafe or mismatch), result.stdout + result.stderr)
        self.assertIn('OMARCHY CYBERPUNK · v0.1.0', result.stdout)
        self.assertNotIn('\x1b', result.stdout)
        self.assertEqual('Ready.' in result.stdout, not (unsafe or mismatch))
        if piped:
            self.assertEqual((self.fixture.home / 'bootstrap-options').read_text(), '--setup\nfull\n--non-interactive\n')

    def test_bootstrap_downloads_latest_and_cleans_temporary_files(self):
        self.bootstrap()

    def test_piped_bootstrap_forwards_unattended_setup_options(self):
        self.bootstrap(piped=True)

    def test_bootstrap_rejects_bad_checksum(self):
        self.bootstrap(mismatch=True)

    def test_bootstrap_rejects_archive_traversal(self):
        self.bootstrap(unsafe=True)
