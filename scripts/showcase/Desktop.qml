import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "Menu" as CyberMenu
import "Notifications" as CyberNotifications
import "Osd" as CyberOsd
import "Picker" as NativePicker

// Actual component QML, rendered over a clean wallpaper in a private HOME/bus.
// No authentication agent, session lock, real notification history or shell host.
ShellRoot {
  id: root
  property string wallpaper: "06.png"
  PanelWindow {
    anchors { top: true; bottom: true; left: true; right: true }
    WlrLayershell.namespace: "cyberpunk-showcase"
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore
    mask: Region {}
    color: "#07090e"
    Image {
      id: backdrop
      anchors.fill: parent
      source: "file://" + Quickshell.env("CYBERPUNK_PREVIEW_ROOT") + "/theme/backgrounds/" + root.wallpaper
      fillMode: Image.PreserveAspectCrop
      asynchronous: false
    }
  }
  CyberMenu.Menu { id: menuWidget }
  CyberNotifications.Service { id: notifications }
  CyberOsd.Osd { id: osdWidget }
  NativePicker.ImagePicker { id: pickerWidget }
  IpcHandler {
    target: "showcase"
    function ready(): string { return backdrop.status === Image.Ready ? "ok" : "loading" }
    function wallpaper(name: string): string { root.wallpaper = name; return "ok" }
    function menu(payload: string): string { menuWidget.open(payload); return "ok" }
    function health(): string { return menuWidget.health() }
    function filter(query: string): string { menuWidget.setFilter(query); return "ok" }
    function move(delta: string): string { menuWidget.select(Number(delta)); return "ok" }
    function closeMenu(): string { menuWidget.cancel(); return "ok" }
    function notificationCount(): string { return String(notifications.popupModel.count) }
    function osd(payload: string): string { osdWidget.open(payload); return "ok" }
    function closeOsd(): string { osdWidget.close(); return "ok" }
    function picker(payload: string): string { pickerWidget.open(payload); return "ok" }
    function pickerReady(): string { return pickerWidget.imagesLoaded && pickerWidget.layoutSettled ? "ok" : "loading" }
    function closePicker(): string { pickerWidget.close(); return "ok" }
  }
}
