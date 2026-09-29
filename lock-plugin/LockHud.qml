import QtQuick
import "LoginLayout.js" as LoginLayout

// Auth-independent presentation. The real field remains in StockLockView;
// loginRequested is connected to that view's existing submitPassword signal.
Item {
    id: hud
    property real fieldWidth: LoginLayout.fieldWidth
    property real fieldHeight: LoginLayout.fieldHeight
    property real fieldYOffset: Math.min(112, height * 0.105)
    property color red: "#ff3045"
    property color cyan: "#53e3d2"
    property color textColor: "#e5f1ee"
    property color mutedColor: "#868c93"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property string userLabel: "LOCAL USER"
    property string topLeftLabel: "//  LOCAL  /  SESSION LOCK"
    property string topRightLabel: "AUTHORIZATION REQUIRED"
    property bool showClock: true
    property string submitLabel: "LOG IN"
    property string hintLabel: "ESC CLEAR  /  ENTER CONFIRM"
    property bool fingerprintMode: false
    property string clock: Qt.formatTime(new Date(), "hh:mm")
    property bool fingerprintAvailable: false
    property bool authenticating: false
    property bool canSubmit: false
    property bool failed: false
    property real signalPulse: 0
    readonly property real fieldCenter: height / 2 + fieldYOffset

    signal loginRequested()

    function scan() { scanner.restart() }
    onFailedChanged: if (failed) scan()
    Timer { interval: 30000; repeat: true; running: hud.showClock; onTriggered: hud.clock = Qt.formatTime(new Date(), "hh:mm") }

    CurvedLabel {
        id: leftLabel
        x: Math.max(18, hud.width * 0.023)
        y: Math.max(18, hud.height * 0.032)
        text: hud.topLeftLabel
        color: hud.red
        fontFamily: hud.fontFamily
    }
    CurvedLabel {
        id: rightLabel
        anchors.right: parent.right
        anchors.rightMargin: Math.max(25, hud.width * 0.031)
        y: Math.max(18, hud.height * 0.029)
        text: hud.showClock ? hud.clock : hud.topRightLabel
        color: hud.red
        fontFamily: hud.fontFamily
        pixelSize: hud.showClock ? Math.min(34, hud.width * 0.025) : 14
        rightSide: true
    }

    Item {
        id: prompt
        width: Math.min(LoginLayout.promptWidth, hud.width * 0.80)
        height: LoginLayout.promptHeight
        x: (hud.width - width) / 2
        y: hud.fieldCenter - hud.fieldHeight / 2 - LoginLayout.fieldY

        Rectangle { x: 0; width: 19; height: 2; color: hud.red; opacity: 0.85 }
        Rectangle { x: 0; width: 2; height: 15; color: hud.red; opacity: 0.85 }
        Rectangle { x: 25; width: parent.width - 50; height: 1; color: hud.red; opacity: 0.64 }
        Rectangle { anchors.right: parent.right; width: 2; height: 15; color: hud.red; opacity: 0.70 }

        Text {
            x: 25
            y: 39
            text: "// AUTHENTICATION SEQUENCE"
            textFormat: Text.PlainText
            color: hud.red
            font.family: hud.fontFamily
            font.pixelSize: 13
            font.bold: true
        }
        Text {
            anchors.right: parent.right
            anchors.rightMargin: 25
            y: 39
            text: "// SIGNAL DESYNC"
            textFormat: Text.PlainText
            color: hud.cyan
            opacity: Math.min(0.85, hud.signalPulse)
            visible: opacity > 0.08
            font.family: hud.fontFamily
            font.pixelSize: 11
        }
        Text {
            x: 25
            y: 78
            text: "USER"
            textFormat: Text.PlainText
            color: hud.mutedColor
            font.family: hud.fontFamily
            font.pixelSize: 12
        }
        Text {
            anchors.right: parent.right
            anchors.rightMargin: 24
            y: 78
            width: Math.min(255, parent.width * 0.61)
            text: hud.userLabel.toUpperCase()
            textFormat: Text.PlainText
            color: hud.textColor
            horizontalAlignment: Text.AlignRight
            font.family: hud.fontFamily
            font.pixelSize: 12
            elide: Text.ElideLeft
        }
        Text {
            x: 24
            y: 97
            text: hud.failed ? "ACCESS DENIED / RETRY" : (hud.authenticating ? "VERIFYING IDENTITY" : (hud.fingerprintMode ? "SENSOR ACTIVE" : "ENTER PASSWORD"))
            textFormat: Text.PlainText
            color: hud.failed ? hud.red : hud.mutedColor
            font.family: hud.fontFamily
            font.pixelSize: 11
        }

        Rectangle {
            id: scannerLine
            x: (prompt.width - hud.fieldWidth) / 2
            width: hud.fieldWidth
            height: 2
            color: hud.red
            opacity: 0
        }
        SequentialAnimation {
            id: scanner
            NumberAnimation { target: scannerLine; property: "opacity"; from: 0; to: 0.73; duration: 65 }
            NumberAnimation { target: scannerLine; property: "y"; from: 111; to: 177; duration: 230 }
            NumberAnimation { target: scannerLine; property: "opacity"; to: 0; duration: 90 }
        }

        Item {
            id: loginButton
            x: (prompt.width - hud.fieldWidth) / 2
            y: LoginLayout.buttonY
            width: hud.fieldWidth
            height: LoginLayout.buttonHeight
            visible: !hud.fingerprintMode
            activeFocusOnTab: true
            Keys.onReturnPressed: hud.loginRequested()
            Keys.onEnterPressed: hud.loginRequested()
            Canvas {
                id: buttonSurface
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.beginPath()
                    ctx.moveTo(22, 0.5)
                    ctx.lineTo(width - 0.5, 0.5)
                    ctx.lineTo(width - 0.5, height - 9)
                    ctx.lineTo(width - 9, height - 0.5)
                    ctx.lineTo(0.5, height - 0.5)
                    ctx.lineTo(0.5, 22)
                    ctx.closePath()
                    ctx.fillStyle = hud.red
                    ctx.globalAlpha = buttonArea.pressed ? 0.25 : 22 / 255
                    ctx.fill()
                    ctx.lineWidth = 1
                    ctx.strokeStyle = hud.red
                    ctx.globalAlpha = buttonArea.containsMouse ? 0.90 : 0.65
                    ctx.stroke()
                    ctx.globalAlpha = 1
                }
            }
            Text {
                anchors.centerIn: parent
                text: hud.submitLabel
                textFormat: Text.PlainText
                color: hud.red
                font.family: hud.fontFamily
                font.pixelSize: 14
                font.bold: true
                font.letterSpacing: 2
            }
            MouseArea {
                id: buttonArea
                anchors.fill: parent
                hoverEnabled: true
                onContainsMouseChanged: buttonSurface.requestPaint()
                onPressedChanged: buttonSurface.requestPaint()
                onClicked: hud.loginRequested()
            }
        }
        Text {
            x: (prompt.width - hud.fieldWidth) / 2
            y: LoginLayout.hintY
            text: hud.fingerprintMode ? "SENSOR ACTIVE  /  ESC ABORT" : (hud.fingerprintAvailable ? "FINGERPRINT AVAILABLE  /  ENTER CONFIRM" : hud.hintLabel)
            textFormat: Text.PlainText
            color: hud.mutedColor
            font.family: hud.fontFamily
            font.pixelSize: 11
        }
    }
}
