// Omarchy notification content and click semantics in a single HUD banner.
// Only the visual frame is custom; Service.qml retains native delivery/history.
import QtQuick
import Quickshell
import qs.Commons
import qs.Ui
import "../NotificationLogic.js" as NotificationLogic

BorderSurface {
  id: root

  property string app: ""
  property string appIcon: ""
  property string summary: ""
  property string body: ""
  property string image: ""
  property string glyph: ""
  property int urgency: 1
  property double timestamp: 0
  property int cornerRadius: 0
  property string fontFamily: ""
  property real availableWidth: Style.space(550)
  property real revealFraction: 1
  property real symbolOpacity: 1

  readonly property bool hovered: hoverTracker.hovered
  readonly property string styledBody: NotificationLogic.styledBody(body, app, appIcon)
  readonly property string smallIconSource: image ? image : iconSource(appIcon)
  readonly property color accentColor: urgency === 0 ? Qt.darker(Color.notifications.countdown, 1.25) : Color.notifications.countdown
  onAccentColorChanged: {
    warningIcon.requestPaint()
    steppedBorder.requestPaint()
    bannerFrame.requestPaint()
  }

  signal closeRequested()
  signal cardClicked()

  function iconSource(icon) {
    var value = String(icon || "")
    if (!value) return ""
    if (value.indexOf("file://") === 0 || value.indexOf("image://") === 0) return value
    if (value.charAt(0) === "/") return Util.fileUrl(value)
    return Quickshell.iconPath(value, true)
  }

  implicitWidth: Math.max(Style.space(180), Math.min(Style.space(550), availableWidth - Style.gapsOut * 2))
  implicitHeight: Math.max(Style.space(64), messageColumn.implicitHeight + Style.space(26))
  radius: 0
  color: "transparent"
  borderSpec: Border.none()

  // The warning triangle stays put while the body is revealed or retracted.
  Canvas {
    id: warningIcon
    width: Style.space(48)
    height: root.height
    opacity: root.symbolOpacity
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
      var ctx = getContext("2d")
      ctx.clearRect(0, 0, width, height)
      ctx.save()
      // Keep the symbol smaller than even a one-line banner and centered as
      // taller, wrapped messages grow around it.
      var apexX = width / 2
      var apexY = height / 2 - Style.space(17)
      var leftX = Style.space(5)
      var rightX = width - leftX
      var baseY = height / 2 + Style.space(17)
      ctx.beginPath()
      ctx.moveTo(apexX, apexY)
      ctx.lineTo(rightX, baseY)
      ctx.lineTo(leftX, baseY)
      ctx.closePath()
      ctx.strokeStyle = String(root.accentColor)
      ctx.shadowColor = ctx.strokeStyle
      ctx.shadowBlur = 6
      ctx.lineWidth = 1.8
      ctx.lineJoin = "bevel"
      ctx.stroke()
      // Reinforce short segments at the three angles rather than increasing
      // the triangle's line width everywhere or rounding its corners.
      ctx.shadowBlur = 3
      ctx.lineWidth = 3.1
      function angle(x, y, ax, ay, bx, by) {
        ctx.beginPath()
        ctx.moveTo(x + (ax - x) * 0.14, y + (ay - y) * 0.14)
        ctx.lineTo(x, y)
        ctx.lineTo(x + (bx - x) * 0.14, y + (by - y) * 0.14)
        ctx.stroke()
      }
      angle(apexX, apexY, leftX, baseY, rightX, baseY)
      angle(rightX, baseY, apexX, apexY, leftX, baseY)
      angle(leftX, baseY, rightX, baseY, apexX, apexY)
      ctx.restore()
    }
  }

  Text {
    width: warningIcon.width
    height: warningIcon.height
    x: warningIcon.x
    // A triangle's visual center lies below the center of its bounding box.
    y: warningIcon.y + Style.space(4)
    opacity: root.symbolOpacity
    text: "!"
    color: root.accentColor
    font.family: root.fontFamily || "monospace"
    font.pixelSize: Style.font.heading
    font.bold: true
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
  }

  // One filled silhouette makes the full-height border and shorter outer
  // stroke pulse as a single shape, without an overlapping frame underneath.
  Canvas {
    id: steppedBorder
    x: warningIcon.width + Style.space(7)
    y: Style.space(5)
    z: 1
    width: Style.space(8)
    height: Math.max(0, root.height - Style.space(10))
    opacity: root.symbolOpacity
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
      var ctx = getContext("2d")
      ctx.clearRect(0, 0, width, height)
      if (width <= 0 || height <= 0) return
      var step = width / 2
      var start = Math.min(height, Style.space(6))
      var end = Math.max(start, height - Style.space(2))
      ctx.beginPath()
      ctx.moveTo(step, 0)
      ctx.lineTo(width, 0)
      ctx.lineTo(width, height)
      ctx.lineTo(step, height)
      ctx.lineTo(step, end)
      ctx.lineTo(0, end)
      ctx.lineTo(0, start)
      ctx.lineTo(step, start)
      ctx.closePath()
      ctx.fillStyle = String(root.accentColor)
      ctx.fill()
    }
  }

  Item {
    id: panelReveal
    x: warningIcon.width + Style.space(6)
    width: Math.max(0, (root.width - x) * root.revealFraction)
    height: root.height
    clip: true

    Item {
      width: root.width - panelReveal.x
      height: root.height

      Canvas {
        id: bannerFrame
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
          var ctx = getContext("2d")
          ctx.clearRect(0, 0, width, height)
          ctx.beginPath()
          ctx.moveTo(5, 5)
          ctx.lineTo(width - 5, 5)
          ctx.lineTo(width - 5, height - 18)
          ctx.lineTo(width - 18, height - 5)
          ctx.lineTo(5, height - 5)
          // Keep the panel fill closed but leave its left edge un-stroked:
          // steppedBorder owns that edge even while the panel is revealing.
          ctx.fillStyle = "rgba(24, 8, 12, 0.95)"
          ctx.fill()
          ctx.save()
          ctx.strokeStyle = String(root.accentColor)
          ctx.shadowColor = ctx.strokeStyle
          ctx.shadowBlur = 12
          ctx.lineWidth = 1.6
          ctx.stroke()
          ctx.restore()
        }
      }

      Image {
        id: mediaIcon
        visible: root.smallIconSource.length > 0 && status !== Image.Error
        x: Style.space(17)
        anchors.verticalCenter: parent.verticalCenter
        width: Style.space(25)
        height: width
        source: root.smallIconSource
        sourceSize.width: width * Screen.devicePixelRatio
        sourceSize.height: height * Screen.devicePixelRatio
        fillMode: Image.PreserveAspectFit
        asynchronous: true
      }

      Text {
        visible: root.glyph.length > 0 && !mediaIcon.visible
        text: root.glyph
        x: Style.space(17)
        anchors.verticalCenter: parent.verticalCenter
        color: root.accentColor
        font.family: root.fontFamily || "monospace"
        font.pixelSize: Style.font.icon
      }

      Column {
        id: messageColumn
        x: Style.space(48)
        width: Math.max(1, parent.width - x - Style.space(16))
        anchors.verticalCenter: parent.verticalCenter
        spacing: Style.space(3)

        Text {
          width: parent.width
          visible: text.length > 0
          text: (root.summary || root.app).toUpperCase()
          textFormat: Text.PlainText
          color: root.accentColor
          font.family: root.fontFamily || "monospace"
          font.pixelSize: Style.font.heading
          font.bold: true
          wrapMode: Text.WordWrap
          horizontalAlignment: Text.AlignHCenter
        }

        Text {
          width: parent.width
          visible: text.length > 0
          text: root.styledBody
          textFormat: Text.StyledText
          color: root.accentColor
          font.family: root.fontFamily || "monospace"
          font.pixelSize: Style.font.body
          wrapMode: Text.WordWrap
          horizontalAlignment: Text.AlignHCenter
        }
      }
    }
  }

  HoverHandler { id: hoverTracker }
  MouseArea {
    anchors.fill: parent
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    onClicked: function(mouse) {
      if (mouse.button === Qt.RightButton) root.closeRequested()
      else root.cardClicked()
    }
  }
}
