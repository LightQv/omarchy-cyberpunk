import QtQuick
import qs.Commons
import qs.Commons as Commons

// Presentation only. Toast.qml retains the native 4.5 notification controls.
Canvas {
  id: root
  property color accent: Commons.Color.notifications.countdown
  onAccentChanged: requestPaint()
  onWidthChanged: requestPaint()
  onHeightChanged: requestPaint()
  onPaint: {
    var ctx = getContext("2d")
    ctx.clearRect(0, 0, width, height)
    if (width < Style.space(100) || height <= 0) return
    var left = Style.space(62)
    var inset = Style.space(5)
    var corner = Math.min(Style.space(13), height / 4)
    ctx.beginPath()
    ctx.moveTo(left, inset)
    ctx.lineTo(width - inset, inset)
    ctx.lineTo(width - inset, height - inset - corner)
    ctx.lineTo(width - inset - corner, height - inset)
    ctx.lineTo(left, height - inset)
    ctx.closePath()
    ctx.fillStyle = "rgba(24, 8, 12, 0.95)"
    ctx.fill()
    ctx.strokeStyle = String(accent)
    ctx.shadowColor = String(accent)
    ctx.shadowBlur = 8
    ctx.lineWidth = 1.6
    ctx.stroke()
    ctx.fillStyle = String(accent)
    ctx.fillRect(left - Style.space(3), inset, Style.space(3), height - inset * 2)
    ctx.fillRect(left - Style.space(7), inset + Style.space(7), Style.space(3), Math.max(0, height - inset * 2 - Style.space(12)))
    var mid = height / 2
    var radius = Math.min(Style.space(19), height / 2 - Style.space(5))
    ctx.beginPath()
    ctx.moveTo(Style.space(27), mid - radius)
    ctx.lineTo(Style.space(27) + radius, mid + radius)
    ctx.lineTo(Style.space(27) - radius, mid + radius)
    ctx.closePath()
    ctx.stroke()
    ctx.shadowBlur = 0
    ctx.font = "bold " + Style.space(23) + "px monospace"
    ctx.textAlign = "center"
    ctx.textBaseline = "middle"
    ctx.fillText("!", Style.space(27), mid + Style.space(5))
  }
}
