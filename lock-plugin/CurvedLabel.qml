import QtQuick

// Subtle shared top-edge HUD lettering: the inner ends dip toward the screen.
Item {
    id: label
    property string text: ""
    property color color: "#ff3045"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property int pixelSize: 14
    property bool rightSide: false
    property real depth: 8
    implicitWidth: glyphMetrics.advanceWidth + 4
    implicitHeight: pixelSize + depth + 5

    TextMetrics {
        id: glyphMetrics
        font.family: label.fontFamily
        font.pixelSize: label.pixelSize
        font.bold: true
        text: label.text
    }
    Canvas {
        id: ink
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.font = "bold " + label.pixelSize + "px '" + label.fontFamily + "'"
            ctx.fillStyle = label.color
            ctx.textBaseline = "alphabetic"
            var total = Math.max(1, glyphMetrics.advanceWidth)
            var advance = 0
            for (var i = 0; i < label.text.length; ++i) {
                var glyph = label.text[i]
                var step = ctx.measureText(glyph).width
                var t = (advance + step / 2) / total
                var inward = label.rightSide ? 1 - t : t
                var slope = (label.rightSide ? -1 : 1) * label.depth / total
                ctx.save()
                ctx.translate(2 + advance, label.pixelSize + 1 + label.depth * inward)
                ctx.rotate(Math.atan(slope))
                ctx.fillText(glyph, 0, 0)
                ctx.restore()
                advance += step
            }
        }
    }
    onTextChanged: ink.requestPaint()
    onColorChanged: ink.requestPaint()
    onFontFamilyChanged: ink.requestPaint()
    onPixelSizeChanged: ink.requestPaint()
    onRightSideChanged: ink.requestPaint()
    onDepthChanged: ink.requestPaint()
}
