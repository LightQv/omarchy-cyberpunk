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
import qs.Commons as Commons
import "Menu" as CyberMenu
import "NativeMenu" as NativeMenu
import "Notifications" as CyberNotifications
import "Osd" as CyberOsd
import "Polkit" as CyberPolkit
import "Lock" as CyberLock

ShellRoot {
  CyberMenu.Menu { id: menu; defaultMenuPath: Quickshell.env("CYBERPUNK_TEST_MENU") }
  NativeMenu.Menu { id: nativeMenu; defaultMenuPath: Quickshell.env("CYBERPUNK_TEST_MENU") }
  CyberNotifications.Service { id: notifications }
  CyberNotifications.Toast {
    id: toast
    row: ({key: "test", summary: "Test", body: "Private fixture", app: "test", urgency: 1})
  }
  CyberNotifications.Toast {
    id: actionable
    row: ({key: "actionable", summary: "Screenshot", urgency: 0})
    actions: [{id: "open", text: "Open"}, {id: "copy", text: "Copy"}]
    property string invoked: ""
    onActionInvoked: function(identifier) { invoked = identifier }
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
        require(menu.rowsLoaded && menu.itemOrder.length === 4, "Menu source loading failed")
        require(menu.item("apps").kind === "menu" && !menu.item("apps").action && menu.item("apps").provider === "apps",
                "Apps escaped to the stock dock launcher")
        require(nativeMenu.item("apps").kind === "action" && nativeMenu.item("apps").action === "omarchy-shell omarchy.dock apps",
                "Native themes lost the stock Apps route")
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
        require(String(toast.accentColor) === String(Commons.Color.notifications.countdown), "Normal accent lost")
        require(String(actionable.accentColor) === String(Qt.darker(Commons.Color.notifications.countdown, 1.25)),
                "Low urgency uses white/text instead of the Cyberpunk accent")
        require(actionable.allDeeds.length === 2 && !actionable.actionsVisible, "Actions clutter the resting banner")
        var restingHeight = actionable.targetHeight
        actionable.hovered = true
        require(actionable.actionsVisible && actionable.targetHeight > restingHeight, "Hover actions unavailable")
        actionable.doDeed(actionable.allDeeds[1])
        require(actionable.invoked === "copy", "Sender action identifier changed")
        actionable.hovered = false
        actionable.selected = true
        require(actionable.actionsVisible, "Keyboard actions unavailable")
        actionable.selected = false
        require(!actionable.actionsVisible, "Actions persist after interaction")
        actionable.row = ({key: "critical", summary: "Critical", urgency: 2})
        require(String(actionable.accentColor) === String(Commons.Color.notifications.countdown), "Critical theme accent lost")
        var surfaces = notifications.surfaceStates()
        require(surfaces.length > 0, "No notification surface")
        for (var i = 0; i < surfaces.length; i++) {
          var surface = surfaces[i]
          require(surface.width > 0 && Math.abs(surface.bannerCenterX - surface.width / 2) <= 1,
                  "Banners are no longer centered")
          require(surface.bannerTop >= surface.height * 0.085 - 1, "Banners lost their 8.5% top inset")
        }
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

MOTION_QML = r'''
import QtQuick
import Quickshell
import qs.Commons as Commons
import "Notifications" as CyberNotifications
import "Notifications/Store.js" as Store

ShellRoot {
  CyberNotifications.Service { id: service }
  CyberNotifications.CyberpunkMotion { id: motion }
  CyberNotifications.CyberpunkMotion { id: interrupted }
  CyberNotifications.CyberpunkMotion { id: still; animated: false }
  CyberNotifications.CyberpunkMotion { id: delayed; animated: false }
  QtObject {
    id: testScene
    property bool jumping: false
    function at(key, what) { return what === "y" ? 0 : 1 }
  }
  CyberNotifications.Toast {
    id: toast
    scene: testScene
    row: ({key: "visual", summary: "Animation fixture", duration: 0})
  }
  property int stage: 0
  function require(value, message) { if (!value) throw new Error(message) }
  Timer {
    id: steps
    interval: 120
    running: true
    onTriggered: {
      try {
        if (stage === 0) {
          require(motion.entering && motion.revealFraction === 0 && motion.symbolOpacity < 0.9,
                  "Warning must blink before the panel appears")
          require(still.revealFraction === 1 && !still.entering, "Static preview must not animate")
          require(toast.revealFraction === 0 && toast.symbolOpacity < 0.9, "Toast did not bind its visual clock")
          delayed.animated = true
          require(delayed.entering && delayed.revealFraction === 0,
                  "Late scene assignment skipped the blink/reveal")
          interrupted.leaving = true
          interval = 420
        } else if (stage === 1) {
          require(interrupted.revealFraction === 0 && !interrupted.entering,
                  "Closing during blink restarted the reveal")
          require(motion.revealFraction === 0, "Text appeared during the first two pulses")
          interval = 520
        } else if (stage === 2) {
          require(motion.revealFraction > 0 && motion.revealFraction < 1,
                  "Third pulse must reveal the panel progressively")
          interval = 540
        } else if (stage === 3) {
          require(motion.revealFraction === 1 && motion.symbolOpacity === 1 && !motion.entering,
                  "Reveal did not settle")
          motion.leaving = true
          toast.place = ({leaving: true, hidden: false, front: true, z: 1})
          service.showRow(Store.normalise({key: "departure", summary: "Fixture", duration: 0}))
          service.showRow(Store.normalise({key: "revive", summary: "Replacement", duration: 0}))
          interval = 120
        } else if (stage === 4) {
          require(motion.revealFraction > 0 && motion.revealFraction < 1 && motion.symbolOpacity === 1,
                  "Exit must retract the panel before fading the warning")
          service.closeToast("departure", "expired")
          service.closeToast("revive", "dismissed")
          require(service.departures.departure.until <= Date.now() + 520,
                  "Departure has an unbounded visual deadline")
          // Control the deadline while testing scene completion: compositor
          // scheduling must not turn a slow CI frame into a timing failure.
          service.departures.departure.until = Date.now() + 2000
          service.finishLeaving()
          require(service.rowIndexFor("departure") >= 0, "Scene retarget bypassed exit deadline")
          service.showRow(Store.normalise({key: "revive", summary: "Updated during exit", duration: 0}))
          interval = 260
        } else if (stage === 5) {
          require(motion.revealFraction === 0 && motion.symbolOpacity < 1,
                  "Warning did not fade after retraction")
          require(service.rowIndexFor("departure") >= 0,
                  "Native scene destroyed the card before its unreveal finished")
          service.finishLeaving()
          require(service.rowIndexFor("departure") >= 0, "Scene retarget bypassed exit deadline")
          service.departures.departure.until = Date.now() - 1
          service.finishDeparted(Date.now())
          interval = 400
        } else if (stage === 6) {
          require(motion.symbolOpacity === 0 && !motion.exiting, "Exit did not finish")
          require(service.rowIndexFor("departure") < 0 && !service.liveKeys.departure,
                  "Departure leaked a row or reservation")
          require(service.rowIndexFor("revive") >= 0 && !service.leaving.revive,
                  "Replacement during unreveal was deleted by an old deadline")
          service.closeToast("revive", "dismissed", true)
          service.showRow(Store.normalise({key: "instant", summary: "Keyboard", duration: 0}))
          motion.leaving = false
          motion.enter()
          motion.interactive = true
          require(motion.revealFraction === 1 && !motion.entering, "Interaction must reveal actions immediately")
          interval = 60
        } else if (stage === 7) {
          service.closeToast("instant", "dismissed", true)
          interval = 60
        } else {
          require(service.rowIndexFor("instant") < 0, "Keyboard dismissal stopped being immediate")
          require(toast.revealFraction === 0 && toast.symbolOpacity === 0, "Toast did not finish its unreveal")
          Commons.Style.reduceMotion = true
          motion.interactive = false
          motion.enter()
          require(motion.revealFraction === 1 && !motion.entering, "Animations-off still blinks")
          motion.leaving = true
          require(motion.revealFraction === 0 && motion.symbolOpacity === 0 && !motion.exiting,
                  "Animations-off still animates departure")
          console.log("CYBERPUNK_MOTION_OK")
          Qt.quit()
          return
        }
        stage++
        steps.start()
      } catch (error) {
        console.error("CYBERPUNK_MOTION_FAILED: " + error)
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
        self.run_components(QML, "CYBERPUNK_45_COMPONENTS_OK")

    def test_blink_reveal_unreveal_and_departure_lifetime(self):
        self.run_components(MOTION_QML, "CYBERPUNK_MOTION_OK")

    def test_centered_text_without_letter_avatar_keeps_real_thumbnails(self):
        self.run_components(r'''
import QtQuick
import Quickshell
import "Notifications" as CyberNotifications
import "Notifications/Store.js" as Store
ShellRoot {
  PanelWindow {
    implicitWidth: 600
    implicitHeight: 360
    color: "transparent"
    mask: Region {}
    CyberNotifications.Toast {
      id: plain
      cardWidth: 550
      row: Store.normalise({key: "plain", app: "CyberpunkMissingFixtureApp", summary: "<b>Centered heading</b>", body: "Centered body", duration: 0})
    }
    CyberNotifications.Toast {
      id: pictured
      y: 100
      cardWidth: 550
      row: Store.normalise({key: "image", app: "CyberpunkMissingFixtureApp", summary: "Screenshot", body: "Thumbnail retained", image: Quickshell.env("CYBERPUNK_TEST_IMAGE"), duration: 0})
    }
    CyberNotifications.Toast {
      id: missing
      y: 200
      cardWidth: 550
      row: Store.normalise({key: "missing", app: "CyberpunkMissingFixtureApp", summary: "Missing image", image: "/nonexistent-cyberpunk-fixture.png", duration: 0})
    }
  }
  function named(item, name) {
    if (item.objectName === name) return item
    for (var child of item.children || []) {
      var found = named(child, name)
      if (found) return found
    }
    return null
  }
  function require(value, message) { if (!value) throw new Error(message) }
  Timer {
    interval: 1500
    running: true
    onTriggered: {
      try {
        for (var toast of [plain, pictured, missing]) {
          var heading = named(toast, "cyberpunk-toast-heading")
          var body = named(toast, "cyberpunk-toast-body")
          var thumb = named(toast, "cyberpunk-toast-thumbnail")
          var column = named(toast, "cyberpunk-toast-text")
          require(heading.horizontalAlignment === Text.AlignHCenter && body.horizontalAlignment === Text.AlignHCenter,
                  "Heading or body is not centered")
          require(Math.abs(heading.mapToItem(toast, 0, 0).x + heading.width / 2
                         - body.mapToItem(toast, 0, 0).x - body.width / 2) < 0.5,
                  "Heading and body have different center axes")
          require(heading.textFormat === Text.PlainText && body.textFormat === Text.StyledText,
                  "Native text safety or link support changed")
          if (toast !== pictured) {
            require(thumb.width === 0 && !thumb.visible, "Empty or letter-avatar slot remains")
            require(Math.abs(column.width - (toast.width - 82)) < 0.5, "Empty avatar still reserves text space")
          } else {
            var image = named(toast, "cyberpunk-toast-picture")
            require(thumb.visible && thumb.width > 0 && image.status === Image.Ready && image.visible,
                    "Real screenshot thumbnail was removed")
          }
        }
        plain.hovered = true
        var title = named(plain, "cyberpunk-toast-heading")
        var text = named(plain, "cyberpunk-toast-body")
        require(Math.abs(title.mapToItem(plain, 0, 0).x + title.width / 2
                       - text.mapToItem(plain, 0, 0).x - text.width / 2) < 0.5,
                "Hover controls shifted heading off center")
        var frame = named(plain, "cyberpunk-toast-frame")
        require(frame.showWarning, "Front card lost its warning")
        plain.place = ({front: false, hidden: false, z: 1})
        require(!frame.showWarning, "Collapsed back card repeats the warning")
        plain.expanded = true
        require(frame.showWarning, "Expanded card lost its warning")
        plain.expanded = false
        require(!frame.showWarning, "Collapsing the stack retained the back warning")
        plain.place = ({front: true, hidden: false, z: 1})
        require(frame.showWarning, "Promoted front card did not regain its warning")
        console.log("CYBERPUNK_CENTERED_TOAST_OK")
        Qt.quit()
      } catch (error) { console.error(error); Qt.exit(1) }
    }
  }
}
''', "CYBERPUNK_CENTERED_TOAST_OK")

    def test_frame_left_edge_is_one_connected_stepped_silhouette(self):
        import base64
        import io
        import re
        from PIL import Image

        output = self.run_components(r'''
import QtQuick
import Quickshell
import qs.Commons
import "Notifications" as CyberNotifications
ShellRoot {
  PanelWindow {
    implicitWidth: Style.space(350)
    implicitHeight: Style.space(180)
    color: "transparent"
    mask: Region {}
    CyberNotifications.CyberpunkFrame { id: shortFrame; width: Style.space(220); height: Style.space(48); accent: "#ff0000" }
    CyberNotifications.CyberpunkFrame { id: tallFrame; y: Style.space(50); width: Style.space(330); height: Style.space(128); accent: "#ff0000"; showWarning: false }
  }
  Timer {
    interval: 300
    running: true
    onTriggered: {
      try {
        for (var frame of [shortFrame, tallFrame]) {
          console.log("CYBERPUNK_FRAME_IMAGE:" + JSON.stringify({
            width: frame.width, height: frame.height, left: Style.space(62), edge: Style.space(3),
            showWarning: frame.showWarning, iconX: Style.space(27),
            image: frame.toDataURL("image/png")
          }))
        }
        console.log("CYBERPUNK_FRAME_EDGE_OK")
        Qt.quit()
      } catch (error) { console.error(error); Qt.exit(1) }
    }
  }
}
''', "CYBERPUNK_FRAME_EDGE_OK")
        frames = re.findall(r"CYBERPUNK_FRAME_IMAGE:(\{.*\})", output)
        self.assertEqual(len(frames), 2, output)
        for encoded in frames:
            frame = json.loads(encoded)
            image = Image.open(io.BytesIO(base64.b64decode(frame["image"].split(",", 1)[1]))).convert("RGBA")
            # Canvas backing pixels follow fractional output scale, not the
            # rounded Screen.devicePixelRatio. Derive the actual render ratio.
            ratio = image.width / frame["width"]
            left, edge = frame["left"], frame["edge"]
            for x in range(int(left - edge * 2), int(left)):
                pixel = image.getpixel((int((x + 0.5) * ratio), int(frame["height"] / 2 * ratio)))
                self.assertEqual(pixel, (255, 0, 0, 255), (frame["height"], x, pixel))
            icon = image.crop((int((frame["iconX"] - 10) * ratio), int((frame["height"] / 2 - 12) * ratio),
                               int((frame["iconX"] + 10) * ratio), int((frame["height"] / 2 + 12) * ratio)))
            maximum_alpha = icon.getchannel("A").getextrema()[1]
            if frame["showWarning"]:
                self.assertGreaterEqual(maximum_alpha, 250, "Front warning was not painted")
            else:
                self.assertLessEqual(maximum_alpha, 5, "Back-card warning is still painted")

    def run_components(self, qml, marker):
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
                "NativeMenu": package / "shell/plugins/menu",
                "Osd": ROOT / "osd-plugin", "Polkit": ROOT / "polkit-plugin",
                "Lock": ROOT / "lock-plugin", "lightqv.cyberpunk-lock": ROOT / "lock-plugin",
            }.items():
                if name in ("Polkit", "lightqv.cyberpunk-lock"):
                    shutil.copytree(target, base / name)
                else:
                    (base / name).symlink_to(target)
            (base / "shell.qml").write_text(qml)
            (base / "menu.jsonc").write_text(json.dumps({
                "root": {"label": "Test"},
                "root.disabled": {"label": "Already installed", "action": "true", "disabled": "true"},
                "root.ready": {"label": "Ready", "action": "true"},
                "apps": {"label": "Apps", "provider": "apps", "action": "omarchy-shell omarchy.dock apps"},
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
                environment["CYBERPUNK_TEST_IMAGE"] = str(ROOT / "theme/backgrounds/01.png")
                result = subprocess.run(["qs", "--no-color", "-p", str(base / "shell.qml")],
                    env=environment, capture_output=True, text=True, timeout=25)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn(marker, output)
                for error in ("ReferenceError:", "TypeError:", "Cannot assign to non-existent", "is not a type", "Binding loop detected"):
                    self.assertNotIn(error, output, output)
                return output
            finally:
                bus.terminate()
                bus.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
