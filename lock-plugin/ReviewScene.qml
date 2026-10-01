import QtQuick
import "PreviewPalette.js" as Palette

// Offline-only artwork scene. No session lock, Polkit registration or input.
Item {
    id: review
    width: 1920
    height: 1080
    property bool polkitMode: false
    property string reviewUserName: "LOCAL USER"
    property real phase: 1
    property url blurredSource: ""
    property url sharpSource: ""

    SignalRhythm { id: rhythm; phase: review.phase; variant: 0 }

    Rectangle { anchors.fill: parent; color: Palette.background }
    Image {
        anchors.fill: parent
        source: review.blurredSource
        asynchronous: false
        fillMode: Image.PreserveAspectCrop
    }
    Rectangle {
        anchors.fill: parent
        color: review.polkitMode ? "#a607090e" : "#170c1015"
    }
    SignalFault {
        anchors.fill: parent
        imageSource: review.sharpSource
        strength: rhythm.intensity
        phase: rhythm.phase
        variant: rhythm.variant
        red: Palette.red
        cyan: Palette.cyan
    }

    LockHud {
        id: hud
        anchors.fill: parent
        red: Palette.red
        cyan: Palette.cyan
        textColor: Palette.text
        mutedColor: Palette.dim
        userLabel: review.reviewUserName
        showClock: !review.polkitMode
        topLeftLabel: review.polkitMode ? "//  LOCAL  /  PRIVILEGED ACCESS" : "//  LOCAL  /  SESSION LOCK"
        topRightLabel: "AUTHORIZATION REQUIRED"
        submitLabel: review.polkitMode ? "SUBMIT" : "LOG IN"
        hintLabel: review.polkitMode ? "ESC ABORT  /  ENTER CONFIRM" : "ESC CLEAR  /  ENTER CONFIRM"
        signalPulse: rhythm.intensity
    }
    Text {
        visible: review.polkitMode
        x: (parent.width - hud.fieldWidth) / 2
        y: hud.fieldCenter - hud.fieldHeight / 2 - 128
        width: hud.fieldWidth
        text: "Authorization is required"
        color: Palette.text
        opacity: 0.8
        font.family: "JetBrainsMono Nerd Font"
        font.pixelSize: 11
    }
    Rectangle {
        id: inputField
        width: hud.fieldWidth
        height: hud.fieldHeight
        anchors.centerIn: parent
        anchors.verticalCenterOffset: hud.fieldYOffset
        property color accent: Palette.red
        color: Qt.rgba(accent.r, accent.g, accent.b, 22 / 255)
        border.color: accent
        border.width: 1
        Rectangle { width: 4; height: parent.height; color: inputField.accent }
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
            width: parent.width - 112
            horizontalAlignment: Text.AlignHCenter
            anchors.verticalCenter: parent.verticalCenter
            text: "ENTER PASSWORD"
            color: review.polkitMode ? Palette.text : Palette.dim
            opacity: review.polkitMode ? 0.5 : 1
            font.family: "JetBrainsMono Nerd Font"
            font.pixelSize: 18
        }
        Rectangle {
            x: 60; y: parent.height * 0.23 + 2
            width: 2; height: parent.height * 0.54 - 4
            color: Palette.red
        }
    }
}
