"""Execute real lifecycle scripts in an isolated HOME with fault-injected native APIs.

The fake shell implements only plugin discovery/selection and lock status. These
tests cover project transactions, not acceptance of Omarchy's own implementation.
"""

import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("menu", "polkit", "notifications", "osd", "lock")
FAKE = r'''#!/usr/bin/python
import json, os, pathlib, subprocess, sys
home = pathlib.Path(os.environ["HOME"])
config = home / ".config/omarchy/shell.json"
theme = home / ".local/state/omarchy/current/theme.name"
control = json.loads((home / "control.json").read_text())
args = sys.argv[1:]
command = " ".join(args)
if command == control.get("fail"):
    sys.exit(23)
c = json.loads(config.read_text())
kinds = ("menu", "polkit", "notifications", "osd", "lock")
def clone(kind): return "lightqv.cyberpunk-" + kind
def stock(kind): return "omarchy." + kind
def present(kind): return (home / ".config/omarchy/plugins" / clone(kind)).is_dir()
def enabled(id):
    if control.get("foreign_active") == id: return False
    if id in c.get("disabledPlugins", []): return False
    if id.startswith("lightqv."): return any(p["id"] == id for p in c["plugins"])
    kind = id.split(".")[-1]
    return not any(p["id"] == clone(kind) for p in c["plugins"])
def disable(kind):
    id = clone(kind)
    c["plugins"] = [p for p in c["plugins"] if p["id"] != id]
    for key in ("disabledPlugins", "cloneSourceRestores"):
        c[key] = [p for p in c.get(key, []) if p not in (id, stock(kind))]
    for section in c["bar"]["layout"].values():
        for i, entry in enumerate(section):
            if entry == id: section[i] = stock(kind)
            elif isinstance(entry, dict) and entry.get("id") == id: entry["id"] = stock(kind)
def save(): config.write_text(json.dumps(c))
if pathlib.Path(sys.argv[0]).name == "omarchy-hyprland-session-locked":
    sys.exit(0 if control.get("locked") else 1)
if pathlib.Path(sys.argv[0]).name == "omarchy-shell":
    if args == ["lock", "status"]:
        locked = bool(control.get("locked"))
        print(json.dumps(dict(locked=locked, requested=locked, sessionLocked=locked,
                              secure=locked, passwordPam=True)))
    elif args == ["shell", "rescanPlugins"]: print("ok")
    else: sys.exit(2)
elif args[:2] == ["plugin", "validate"]: pass
elif args == ["plugin", "list", "--json"]:
    result = []
    for kind in kinds:
        result.append(dict(id=stock(kind), enabled=enabled(stock(kind))))
        if present(kind): result.append(dict(id=clone(kind), enabled=enabled(clone(kind)), clonedFrom=stock(kind)))
    if control.get("foreign_active"):
        result.append(dict(id="foreign.clone", enabled=True, clonedFrom=control["foreign_active"]))
    print(json.dumps(result))
elif args[:2] in (["plugin", "enable"], ["plugin", "disable"]):
    id = args[2]; kind = id.split("-")[-1] if id.startswith("lightqv.") else id.split(".")[-1]
    if id.startswith("lightqv.") and not present(kind): sys.exit(2)
    if args[1] == "disable":
        if id.startswith("lightqv."): disable(kind)
        elif id not in c["disabledPlugins"]: c["disabledPlugins"].append(id)
    elif id.startswith("lightqv."):
        disable(kind)
        c["plugins"].append(dict(id=id))
        for section in c["bar"]["layout"].values():
            for i, entry in enumerate(section):
                if entry == stock(kind): section[i] = id
                elif isinstance(entry, dict) and entry.get("id") == stock(kind): entry["id"] = id
    else: disable(kind)
    save()
elif args[:2] == ["plugin", "remove"]:
    (home / ".config/omarchy/plugins" / args[2]).unlink()
elif args[:2] == ["theme", "set"]:
    theme.write_text(args[2] + "\n")
    if control.get("fail_after_theme"):
        sys.exit(24)
    project = pathlib.Path(os.environ["TEST_PROJECT"])
    hook = home / ".config/omarchy/hooks/theme-set.d/lightqv-cyberpunk-menu"
    if hook.exists():
        code = subprocess.call([str(project / "scripts/verify"), "--repair"])
        if control.get("change_after_theme"):
            theme.write_text(control["change_after_theme"] + "\n")
        sys.exit(code)
elif args == ["menu", "ping"]: print("ok")
elif args == ["menu", "close"]: pass
else: sys.exit(2)
'''


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.project = base / "checkout: with spaces"
        self.project.mkdir()
        for directory in ("scripts", "hooks", "theme", "askpass", "menu-plugin", "polkit-plugin",
                          "notifications-plugin", "osd-plugin", "lock-plugin"):
            shutil.copytree(ROOT / directory, self.project / directory,
                            ignore=shutil.ignore_patterns("backgrounds", "__pycache__"))
        for script in ("render-palette", "build-lock"):
            (self.project / "scripts" / script).write_text("#!/bin/bash\nexit 0\n")
        art = self.project / "theme/backgrounds"
        art.mkdir()
        for name in ("01-lucy.png", "03-night-city.jpg"):
            (art / name).touch()
        self.home = base / "home"
        self.config = self.home / ".config/omarchy/shell.json"
        self.config.parent.mkdir(parents=True)
        self.original = {"plugins": [{"id": "unrelated.plugin", "settings": {"keep": 7}}],
                         "disabledPlugins": ["unrelated.disabled"], "cloneSourceRestores": [],
                         "bar": {"layout": {"left": [{"id": "omarchy.menu", "settings": {"keep": 9}}]}},
                         "idle": {"lock": 600}, "unrelated": {"keep": True}}
        self.config.write_text(json.dumps(self.original))
        self.bashrc = self.home / ".bashrc"
        self.bashrc.write_text("# user's configuration\nexport KEEP=1\n")
        self.bashrc.chmod(0o640)
        self.theme = self.home / ".local/state/omarchy/current/theme.name"
        self.theme.parent.mkdir(parents=True)
        self.theme.write_text("matte-black\n")
        self.control = self.home / "control.json"
        self.control.write_text("{}")
        binary = base / "bin"
        binary.mkdir()
        for name in ("omarchy", "omarchy-shell", "omarchy-hyprland-session-locked"):
            path = binary / name
            path.write_text(FAKE)
            path.chmod(0o755)
        runtime = base / "runtime"
        runtime.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), XDG_RUNTIME_DIR=str(runtime),
                        PATH=f"{binary}:{os.environ['PATH']}", TEST_PROJECT=str(self.project),
                        PYTHONDONTWRITEBYTECODE="1")

    def run_script(self, name, *args, success=True):
        result = subprocess.run([str(self.project / "scripts" / name), *args], env=self.env,
                                capture_output=True, text=True, timeout=25)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def removed(self):
        self.run_script("verify", "--removed")
        self.assertEqual(json.loads(self.config.read_text()), self.original)
        self.assertEqual(self.bashrc.read_text(), "# user's configuration\nexport KEEP=1\n")
        self.assertEqual(self.bashrc.stat().st_mode & 0o777, 0o640)
        self.assertTrue((self.project / ".state/safe-mode").exists())

    def test_clean_first_install_and_idempotent_removal(self):
        backup = self.home / ".local/state/omarchy-cyberpunk-backup"
        self.assertFalse(backup.exists())
        self.run_script("install-dev")
        self.assertEqual(json.loads((backup / "shell.json").read_text()), self.original)
        self.assertEqual((backup / "bashrc").stat().st_mode & 0o777, 0o600)
        baseline = (backup / "bashrc").read_bytes()
        self.run_script("uninstall-dev")
        self.removed()
        self.run_script("uninstall-dev")
        self.run_script("install-dev")
        self.assertEqual((backup / "bashrc").read_bytes(), baseline)
        self.run_script("uninstall-dev")
        self.removed()

    def test_install_failure_rolls_back_after_theme_change(self):
        self.control.write_text(json.dumps({"fail_after_theme": True}))
        self.run_script("install-dev", success=False)
        # The injected failure also affects restoration, leaving a retryable state.
        self.control.write_text("{}")
        self.run_script("uninstall-dev")
        self.removed()

    def test_install_failure_before_theme_selection(self):
        self.control.write_text(json.dumps({"fail": "shell rescanPlugins"}))
        # Fault applies to both install and rollback; retry must recover either.
        self.run_script("install-dev", success=False)
        self.control.write_text("{}")
        self.run_script("uninstall-dev")
        self.removed()

    def test_missing_links_and_stale_clone_references(self):
        self.run_script("install-dev")
        for path in (self.home / ".config/omarchy/plugins").iterdir():
            path.unlink()
        (self.home / ".config/omarchy/themes/cyberpunk").unlink()
        self.run_script("uninstall-dev")
        self.removed()

    def test_interrupted_removal_can_resume(self):
        self.run_script("install-dev")
        self.control.write_text(json.dumps({"fail": "plugin remove lightqv.cyberpunk-polkit --yes"}))
        self.run_script("uninstall-dev", success=False)
        self.assertFalse((self.home / ".config/omarchy/plugins/lightqv.cyberpunk-menu").exists())
        self.control.write_text("{}")
        self.run_script("uninstall-dev")
        self.removed()

    def test_concurrent_theme_selection_is_preserved_on_rollback(self):
        self.control.write_text(json.dumps({"change_after_theme": "osaka-jade"}))
        result = self.run_script("install-dev", success=False)
        self.assertIn("theme changed during installation", result.stderr)
        self.assertEqual(self.theme.read_text(), "osaka-jade\n")
        self.removed()

    def test_foreign_link_or_changed_bash_stanza_is_not_overwritten(self):
        self.run_script("install-dev")
        path = self.home / ".config/omarchy/plugins/lightqv.cyberpunk-menu"
        path.unlink()
        path.symlink_to(self.project / "polkit-plugin")
        before = self.config.read_bytes()
        self.run_script("uninstall-dev", success=False)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(path.readlink(), self.project / "polkit-plugin")
        path.unlink()
        path.symlink_to(self.project / "menu-plugin")
        self.bashrc.write_text(self.bashrc.read_text().replace("[[ -r", "[[ -f"))
        self.run_script("uninstall-dev", success=False)
        self.assertEqual(self.config.read_bytes(), before)

    def test_secure_lock_blocks_removal_and_lifecycle_commands_serialize(self):
        self.run_script("install-dev")
        self.control.write_text(json.dumps({"locked": True}))
        before = self.config.read_bytes()
        self.run_script("uninstall-dev", success=False)
        self.assertEqual(self.config.read_bytes(), before)
        self.control.write_text("{}")
        lock = Path(self.env["XDG_RUNTIME_DIR"]) / "lightqv-cyberpunk-lifecycle.lock.operation"
        with lock.open("w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_script("uninstall-dev", success=False)
            self.assertIn("another install/removal", result.stderr)

    def test_incomplete_baseline_is_not_overwritten(self):
        backup = self.home / ".local/state/omarchy-cyberpunk-backup"
        backup.mkdir()
        (backup / "bashrc").write_text("old baseline\n")
        self.run_script("install-dev", success=False)
        self.assertEqual((backup / "bashrc").read_text(), "old baseline\n")
        self.assertEqual(json.loads(self.config.read_text()), self.original)

    def test_new_foreign_active_clone_is_not_disabled_by_removal(self):
        self.run_script("install-dev")
        self.control.write_text(json.dumps({"foreign_active": "omarchy.menu"}))
        before = self.config.read_bytes()
        stanza = self.bashrc.read_bytes()
        result = self.run_script("uninstall-dev", success=False)
        self.assertIn("another active clone", result.stderr)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(self.bashrc.read_bytes(), stanza)
        self.assertTrue((self.home / ".config/omarchy/hooks/theme-set.d/lightqv-cyberpunk-menu").is_symlink())
