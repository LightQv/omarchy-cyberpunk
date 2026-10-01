import QtQuick
import QtQuick.Window
import "PreviewPalette.js" as Palette

// Standalone artwork preview. It never creates WlSessionLock or PAM contexts.
Window {
    id: preview
    property bool showcaseGlitch: Qt.application.arguments.indexOf("glitch") !== -1
    property bool recordDemo: Qt.application.arguments.indexOf("record") !== -1

    SignalRhythm { id: rhythm }
    Timer { interval: 1800; repeat: true; running: preview.recordDemo; onTriggered: rhythm.play() }
    width: 1440
    height: 810
    visible: true
    visibility: Window.FullScreen
    title: "Cyberpunk lock - artwork preview only"
    color: Palette.background

    Image {
        id: wallpaper
        anchors.fill: parent
        source: ".preview/blurred.png"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        onStatusChanged: {
            if (status === Image.Error && source.toString().indexOf("blurred.png") !== -1)
                source = "../theme/backgrounds/01-lucy.png"
        }
    }
    Rectangle { anchors.fill: parent; color: "#26090c11" }

    SignalFault {
        anchors.fill: parent
        // Same still scene as the blurred backdrop, before blur was applied.
        imageSource: "../theme/backgrounds/01-lucy.png"
        strength: preview.showcaseGlitch ? 0.90 : rhythm.intensity
        phase: preview.showcaseGlitch ? 0.60 : rhythm.phase
        variant: preview.showcaseGlitch ? 0 : rhythm.variant
        red: Palette.red
        cyan: Palette.cyan
    }

    // Matches the size and position of the stock Omarchy field; this mock has
    // no password handler or access to the secure lock service.
    Rectangle {
        id: field
        width: 381
        height: 54
        anchors.centerIn: parent
        anchors.verticalCenterOffset: Math.min(112, preview.height * 0.105)
        property color accent: Palette.red
        color: Qt.rgba(accent.r, accent.g, accent.b, 22 / 255)
        border.color: accent; border.width: 1
        Rectangle { width: 4; height: parent.height; color: field.accent }
        Text {
            x: 24
            anchors.verticalCenter: parent.verticalCenter
            text: ">"
            color: Palette.red
            font.family: "JetBrainsMono Nerd Font"
            font.pixelSize: 19
        }
        Text {
            x: 56
            anchors.verticalCenter: parent.verticalCenter
            text: "ENTER PASSWORD"
            visible: false
            color: Palette.dim
            font.family: "JetBrainsMono Nerd Font"
            font.pixelSize: 18
        }
        // Sample shapes only: this mock has no password or PAM service.
        Canvas {
            x: 56
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 80
            height: parent.height * 0.54
            onPaint: {
                var ctx = getContext("2d")
                var count = 7
                var step = 20
                var glyph = 14
                for (var i = 0; i < count; i++) {
                    var left = i * step
                    ctx.beginPath()
                    ctx.moveTo(left + 1, 0)
                    ctx.lineTo(left + glyph, 0)
                    ctx.lineTo(left + glyph, height - 5)
                    ctx.lineTo(left + glyph - 5, height)
                    ctx.lineTo(left + 1, height)
                    ctx.closePath()
                    ctx.fillStyle = "#32ff435b"
                    ctx.fill()
                    ctx.lineWidth = 1.4
                    ctx.strokeStyle = "#ff435b"
                    ctx.stroke()
                }
                ctx.fillStyle = "#ff6474"
                ctx.fillRect(count * step + 2, 2, 2, height - 4)
            }
        }
    }

    LockHud {
        id: hud
        anchors.fill: parent
        red: Palette.red
        cyan: Palette.cyan
        textColor: Palette.text
        mutedColor: Palette.dim
        userLabel: "LOCAL USER"
        signalPulse: preview.showcaseGlitch ? 0.90 : rhythm.intensity
    }
    Text {
        x: 24
        y: 20
        text: preview.showcaseGlitch ? "SIGNAL FAULT  //  NO AUTHENTICATION" : "SAMPLE MASKS  //  NO AUTHENTICATION"
        color: Palette.cyan
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: 12
        opacity: 0.7
    }
    Component.onCompleted: { hud.scan(); if (!showcaseGlitch) rhythm.play() }
}
