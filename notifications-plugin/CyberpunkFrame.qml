import QtQuick
import qs.Commons
import qs.Commons as Commons

// Presentation only. Toast.qml retains the native 4.5 notification controls.
Canvas {
  id: root
  property color accent: Commons.Color.notifications.countdown
  property real revealFraction: 1
  property real symbolOpacity: 1
  property bool showWarning: true
  onShowWarningChanged: requestPaint()
  onRevealFractionChanged: requestPaint()
  onSymbolOpacityChanged: requestPaint()
  onAccentChanged: requestPaint()
  onWidthChanged: requestPaint()
  onHeightChanged: requestPaint()
  onPaint: {
    var ctx = getContext("2d")
    ctx.clearRect(0, 0, width, height)
    ctx.globalAlpha = 1
    if (width < Style.space(100) || height <= 0) return
    var left = Style.space(62)
    var inset = Style.space(5)
    var corner = Math.min(Style.space(13), height / 4)
    ctx.save()
    ctx.beginPath()
    ctx.rect(left, 0, Math.max(0, width - left) * revealFraction, height)
    ctx.clip()
    ctx.beginPath()
    ctx.moveTo(left, inset)
    ctx.lineTo(width - inset, inset)
    ctx.lineTo(width - inset, height - inset - corner)
    ctx.lineTo(width - inset - corner, height - inset)
    ctx.lineTo(left, height - inset)
    ctx.fillStyle = "rgba(24, 8, 12, 0.95)"
    ctx.fill()
    ctx.strokeStyle = String(accent)
    ctx.shadowColor = String(accent)
    ctx.shadowBlur = 8
    ctx.lineWidth = 1.6
    ctx.stroke()
    ctx.restore()
    ctx.globalAlpha = symbolOpacity
    ctx.fillStyle = String(accent)
    ctx.strokeStyle = String(accent)
    ctx.shadowColor = String(accent)
    ctx.shadowBlur = 8
    ctx.lineWidth = 1.6
    // One silhouette: the shorter outer shoulder touches the full-height
    // edge, without a transparent seam or overlapping alpha during a blink.
    var edge = Style.space(3)
    var shoulderTop = Math.min(height - inset, inset + Style.space(7))
    var shoulderBottom = Math.max(shoulderTop, height - inset - Style.space(5))
    ctx.beginPath()
    ctx.moveTo(left - edge, inset)
    ctx.lineTo(left, inset)
    ctx.lineTo(left, height - inset)
    ctx.lineTo(left - edge, height - inset)
    ctx.lineTo(left - edge, shoulderBottom)
    ctx.lineTo(left - edge * 2, shoulderBottom)
    ctx.lineTo(left - edge * 2, shoulderTop)
    ctx.lineTo(left - edge, shoulderTop)
    ctx.closePath()
    ctx.fill()
    // Back cards retain their panel/stepped edge, not another warning icon.
    if (!showWarning) return
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
