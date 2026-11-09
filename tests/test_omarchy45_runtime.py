"""Opt-in component checks against an extracted 4.5 package, never the live shell.

OMARCHY_TEST_ROOT must name usr/share/omarchy inside a verified package. Both
D-Bus addresses and HOME/runtime/config/state directories are private. The test
does not instantiate a session-lock service or run PAM. It uses the existing
Wayland connection for Quickshell's layer-shell backend, without switching live
providers or opening its menu/OSD. Empty notification surfaces are short-lived.
"""

import os
import json
import hashlib
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = os.environ.get("OMARCHY_TEST_ROOT")

QML = r'''
import QtQuick
import Quickshell
import "Menu" as CyberMenu
import "Notifications" as CyberNotifications
import "Osd" as CyberOsd
import "Polkit" as CyberPolkit
import "Lock" as CyberLock

ShellRoot {
  CyberMenu.Menu { id: menu; defaultMenuPath: Quickshell.env("CYBERPUNK_TEST_MENU") }
  CyberNotifications.Service { id: notifications }
  CyberNotifications.Toast {
    id: toast
    row: ({key: "test", summary: "Test", body: "Private fixture", app: "test", urgency: 1})
  }
  CyberOsd.Osd { id: osd }
  CyberPolkit.PolkitAgent { id: polkit }
  CyberLock.CyberpunkLockView { id: lockView; inputEnabled: false; loadBackground: false }
  function require(value, message) {
    if (!value) throw new Error(message)
  }
  Timer {
    interval: 1800
    running: true
    onTriggered: {
      try {
        require(menu.identity() === "cyberpunk-menu-hud-3", "HUD identity lost")
        require(menu.rowsLoaded && menu.itemOrder.length === 3, "Menu source loading failed")
        menu.rebuildDisplay()
        menu.select(1)
        require(menu.rowSelectable(menu.selectedIndex), "Wheel selected a disabled row")
        require(JSON.parse(menu.health()).scannerSlots === 11, "HUD wheel buffer lost")
        menu.mode = "select"
        menu.dmenuMultiple = true
        menu.dmenuOptions = ["first", "second"]
        menu.rebuildDisplay()
        require(menu.dmenuMultiple && JSON.parse(menu.health()).rows === 3, "Native multiple selection missing")
        menu.close()
        require(typeof osd.open === "function" && typeof osd.close === "function", "OSD contract changed")
        require(typeof notifications.runShortcut === "function", "Notification shortcut bridge missing")
        require(notifications.runShortcut("act"), "Notification act IPC missing")
        require(notifications.runShortcut("keyboard"), "Notification keyboard IPC missing")
        require(toast.targetHeight > 0 && toast.allDeeds.length === 0, "Native toast content failed")
        require(typeof lockView.dropsAutoRepeat === "function" && lockView.dropsAutoRepeat(Qt.Key_A), "Wake-key repeat protection lost")
        require(!lockView.dropsAutoRepeat(Qt.Key_Backspace), "Backspace repeat broken")
        console.log("CYBERPUNK_45_COMPONENTS_OK")
        Qt.quit()
      } catch (error) {
        console.error("CYBERPUNK_45_COMPONENTS_FAILED: " + error)
        Qt.exit(1)
      }
    }
  }
}
'''


@unittest.skipUnless(PACKAGE, "Set OMARCHY_TEST_ROOT to a verified 4.5 package tree")
class Omarchy45RuntimeTest(unittest.TestCase):
    def test_pinned_package_and_lock_generator(self):
        package = Path(PACKAGE)
        baseline = json.loads((ROOT / "scripts/omarchy-baseline.json").read_text())
        for name, digest in baseline["files"].items():
            self.assertEqual(hashlib.sha256((package / name).read_bytes()).hexdigest(), digest, name)
        result = subprocess.run(["python", "-B", str(ROOT / "scripts/build-lock"), "--check", "--omarchy-root", str(package)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_components_load_and_keep_native_contracts(self):
        package = Path(PACKAGE)
        with tempfile.TemporaryDirectory(prefix="cyberpunk-45-test-", dir="/tmp/opencode") as directory:
            base = Path(directory)
            home = base / "home"
            current = home / ".local/state/omarchy/current"
            current.mkdir(parents=True)
            (current / "theme").symlink_to(ROOT / "theme")
            (current / "background").symlink_to(ROOT / "theme/backgrounds/01.png")
            runtime = base / "runtime"
            runtime.mkdir(mode=0o700)
            for name, target in {
                "Commons": package / "shell/Commons", "Ui": package / "shell/Ui",
                "Menu": ROOT / "menu-plugin", "Notifications": ROOT / "notifications-plugin",
                "Osd": ROOT / "osd-plugin", "Polkit": ROOT / "polkit-plugin",
                "Lock": ROOT / "lock-plugin", "lightqv.cyberpunk-lock": ROOT / "lock-plugin",
            }.items():
                if name in ("Polkit", "lightqv.cyberpunk-lock"):
                    shutil.copytree(target, base / name)
                else:
                    (base / name).symlink_to(target)
            (base / "shell.qml").write_text(QML)
            (base / "menu.jsonc").write_text(json.dumps({
                "root": {"label": "Test"},
                "root.disabled": {"label": "Already installed", "action": "true", "disabled": "true"},
                "root.ready": {"label": "Ready", "action": "true"},
            }))
            config = base / "bus.conf"
            config.write_text(f'''<busconfig><type>session</type><listen>unix:tmpdir={base}</listen>
<auth>EXTERNAL</auth><policy context="default"><allow own="*"/><allow send_destination="*"/>
<allow receive_sender="*"/></policy></busconfig>''')
            bus = subprocess.Popen(["dbus-daemon", "--nofork", "--config-file=" + str(config), "--print-address=1"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                address = bus.stdout.readline().strip()
                self.assertTrue(address)
                wayland = Path(os.environ["WAYLAND_DISPLAY"])
                if not wayland.is_absolute():
                    wayland = Path(os.environ["XDG_RUNTIME_DIR"]) / wayland
                environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                    XDG_STATE_HOME=str(home / ".local/state"), XDG_DATA_HOME=str(home / ".local/share"),
                    XDG_RUNTIME_DIR=str(runtime), DBUS_SESSION_BUS_ADDRESS=address, DBUS_SYSTEM_BUS_ADDRESS=address,
                    WAYLAND_DISPLAY=str(wayland), OMARCHY_PATH=str(package), QT_QPA_PLATFORM="wayland",
                    CYBERPUNK_TEST_MENU=str(base / "menu.jsonc"), NO_AT_BRIDGE="1", QT_ACCESSIBILITY="0")
                result = subprocess.run(["qs", "--no-color", "-p", str(base / "shell.qml")],
                    env=environment, capture_output=True, text=True, timeout=25)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn("CYBERPUNK_45_COMPONENTS_OK", output)
                for error in ("ReferenceError:", "TypeError:", "Cannot assign to non-existent", "is not a type", "Binding loop detected"):
                    self.assertNotIn(error, output, output)
            finally:
                bus.terminate()
                bus.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
