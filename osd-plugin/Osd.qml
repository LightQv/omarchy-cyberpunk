// Omarchy OSD contract with a theme-scoped Cyberpunk volume-bar presentation.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import "OsdModel.js" as OsdModel

Item {
  id: root

  property bool opened: false
  property string icon: ""
  property string message: ""
  property string iconKey: ""
  property int value: 0
  property int maxValue: 100
  property bool hasProgress: true
  property int duration: 1200

  readonly property bool volumeOsd: iconKey.indexOf("volume") === 0 || iconKey === "mute" || iconKey === "muted"
  readonly property bool muted: volumeOsd && (iconKey.indexOf("mute") !== -1 || value === 0)
  readonly property bool longMessage: !hasProgress && message.length > 0
  readonly property color accent: muted ? Color.menu.selectedBorder : Color.menu.selectedText
  readonly property color barColor: muted ? Color.menu.selectedBorder : Color.menu.border
  readonly property string label: volumeOsd ? "VOLUME" :
    (iconKey.indexOf("microphone") === 0 || iconKey.indexOf("mic") === 0) ? "MICROPHONE" :
    (iconKey === "brightness" || iconKey === "display") ? "BRIGHTNESS" :
    (iconKey.indexOf("media") === 0 || iconKey.indexOf("player") === 0) ? "MEDIA" :
    iconKey ? iconKey.replace(/[-_]/g, " ").toUpperCase() : "STATUS"

  function show(iconName, rawMessage, rawValue, rawMax, rawProgressText, rawDuration) {
    var next = OsdModel.stateForShow(iconName, rawMessage, rawValue, rawMax, rawProgressText, rawDuration)
    iconKey = next.iconKey
    maxValue = next.maxValue
    hasProgress = next.hasProgress
    value = next.value
    message = next.message
    icon = next.icon
    duration = next.duration
    opened = true
    if (duration > 0) hideTimer.restart()
    else hideTimer.stop()
  }

  function open(payloadJson) {
    try {
      var p = JSON.parse(payloadJson || "{}")
      show(p.icon || "", p.message || "", p.value === undefined ? "" : String(p.value), p.max === undefined ? "100" : String(p.max), p.progressText || "", p.duration === undefined ? "1200" : String(p.duration))
    } catch (e) {}
  }

  function close() { opened = false }

  Timer {
    id: hideTimer
    interval: root.duration
    onTriggered: root.opened = false
  }

  IpcHandler {
    target: "osd"
    function show(payloadJson: string): string { root.open(payloadJson); return "ok" }
    function close(): string { root.close(); return "ok" }
    function state(): string { return root.opened ? "open" : "closed" }
    function ping(): string { return "ok" }
  }

  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-osd"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore
    mask: Region {}

    Item {
      id: card
      width: Math.min(Style.space(350), panel.width - Style.gapsOut * 2)
      height: Style.space(62)
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: Math.max(Style.space(68), Math.round(panel.height * 0.13))

      Text {
        id: glyph
        x: 0
        y: Style.space(3)
        width: Style.space(34)
        height: Style.space(29)
        text: root.icon
        textFormat: Text.PlainText
        color: root.accent
        font.family: Style.font.family
        font.pixelSize: Style.font.iconLarge
        style: Text.Outline
        styleColor: "#091015"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
      }
      Text {
        x: Style.space(42)
        y: Style.space(9)
        width: card.width - x - Style.space(84)
        visible: !root.longMessage
        text: root.label
        textFormat: Text.PlainText
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: Style.font.body + 1
        font.bold: true
        color: root.accent
        style: Text.Outline
        styleColor: "#091015"
        elide: Text.ElideRight
      }
      Text {
        x: root.longMessage ? Style.space(42) : card.width - width - Style.space(8)
        y: Style.space(9)
        width: root.longMessage ? card.width - x - Style.space(8) : Style.space(68)
        text: root.message
        textFormat: Text.PlainText
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: Style.font.body + 1
        font.bold: true
        horizontalAlignment: root.longMessage ? Text.AlignLeft : Text.AlignRight
        color: root.accent
        style: Text.Outline
        styleColor: "#091015"
        elide: Text.ElideRight
      }
      Item {
        id: progress
        x: Style.space(42)
        y: Style.space(34)
        width: Math.max(0, card.width - x - Style.space(8))
        height: Style.space(22)
        visible: root.hasProgress

        Rectangle {
          width: parent.width
          height: Math.max(2, Style.space(3))
          anchors.verticalCenter: parent.verticalCenter
          color: Qt.rgba(root.barColor.r, root.barColor.g, root.barColor.b, 0.28)
        }

        Canvas {
          id: glow
          anchors.fill: parent
          property real fillWidth: root.hasProgress ? progress.width * root.value / root.maxValue : 0
          onFillWidthChanged: requestPaint()
          onWidthChanged: requestPaint()
          onHeightChanged: requestPaint()
          Behavior on fillWidth {
            enabled: root.opened
            NumberAnimation { duration: 140; easing.type: Easing.OutCubic }
          }
          Connections {
            target: root
            function onAccentChanged() { glow.requestPaint() }
            function onBarColorChanged() { glow.requestPaint() }
          }
          onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            if (fillWidth <= 0) return
            ctx.beginPath()
            ctx.moveTo(0, height / 2)
            ctx.lineTo(Math.min(width, fillWidth), height / 2)
            ctx.strokeStyle = String(root.barColor)
            ctx.shadowColor = ctx.strokeStyle
            ctx.shadowBlur = Style.space(16)
            ctx.lineWidth = Math.max(4, Style.space(5))
            ctx.stroke()
            // A narrow, bright core reads as neon even over a light wallpaper.
            ctx.shadowBlur = 0
            ctx.strokeStyle = String(root.accent)
            ctx.lineWidth = Math.max(2, Style.space(2))
            ctx.stroke()
          }
        }

        Rectangle {
          width: Math.max(2, Style.space(2))
          height: Style.space(11)
          x: Math.max(0, Math.min(parent.width - width, glow.fillWidth - width / 2))
          anchors.verticalCenter: parent.verticalCenter
          visible: glow.fillWidth > 0
          color: "#f5fffc"
        }
      }
    }
  }
}
