import QtQuick 2.15
import SddmComponents 2.0
import "palette.js" as Palette
import "layout.js" as Layout

Rectangle {
    id: root
    width: 1280
    height: 720
    color: Palette.background
    property bool loginFailed: false
    property bool authenticating: false
    onAuthenticatingChanged: masks.requestPaint()
    property bool succeeded: false
    property int sessionIndex: {
        for (var i = 0; i < sessionModel.rowCount(); i++) {
            var name = String(sessionModel.data(sessionModel.index(i, 0), Qt.DisplayRole) || "")
            if (name.indexOf("uwsm") !== -1) return i
        }
        return sessionModel.lastIndex
    }
    property string sessionName: sessionIndex < 0 ? "DEFAULT SESSION" :
        String(sessionModel.data(sessionModel.index(sessionIndex, 0), Qt.DisplayRole) || "DEFAULT SESSION")
    readonly property real inset: Math.max(25, width * 0.05)

    function login() {
        if (authenticating || !userName.text || !password.text) return
        loginFailed = false
        succeeded = false
        authenticating = true
        sddm.login(userName.text, password.text, sessionIndex)
    }
    function changeSession(step) {
        var count = sessionModel.rowCount()
        if (count > 1) sessionIndex = ((sessionIndex + step) % count + count) % count
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            root.authenticating = false
            root.loginFailed = true
            password.text = ""
            password.forceActiveFocus()
            scan.restart()
        }
        function onLoginSucceeded() { root.succeeded = true }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Palette.burgundy }
            GradientStop { position: 0.49; color: Palette.background }
            GradientStop { position: 1; color: Palette.dark }
        }
    }
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "#55301a23" }
            GradientStop { position: 0.38; color: "#001b1118" }
            GradientStop { position: 1; color: "#8807080d" }
        }
    }
    Rectangle { x: inset; y: root.height * 0.09; width: root.width - 2 * inset; height: 2; color: Palette.red; opacity: 0.8 }
    Rectangle { x: inset; y: root.height * 0.86; width: root.width - 2 * inset; height: 1; color: Palette.red; opacity: 0.65 }
    Rectangle { x: inset; y: root.height * 0.092; width: Math.min(140, root.width * 0.12); height: 3; color: Palette.red }
    Item {
        x: Math.max(9, root.width * 0.013); y: root.height * 0.03
        width: 18; height: root.height * 0.91
        Rectangle { width: 1; height: parent.height; color: Palette.red; opacity: 0.25 }
        Column {
            x: 4; spacing: Math.max(9, root.height * 0.016)
            Repeater {
                model: ["01", "│", "∟", "110", "⋮", "03", "░", "│", "07", "··", "01", "∟", "101", "⋮", "02", "│", "⌁", "11", "│", "00", "⋮", "∟", "07", "│", "10"]
                Text { text: modelData; color: Palette.red; opacity: index % 5 === 0 ? 0.72 : 0.40; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 8 }
            }
        }
    }
    Item {
        x: root.width - Math.max(32, root.width * 0.017); y: root.height * 0.035
        width: 18; height: root.height * 0.90
        Rectangle { width: 1; height: parent.height; color: Palette.red; opacity: 0.25 }
        Column {
            x: -12; spacing: Math.max(9, root.height * 0.016)
            Repeater {
                model: ["10", "⋮", "01", "┐", "001", "░", "│", "11", "⋮", "03", "│", "101", "┐", "00", "│", "01", "⋮", "07", "░", "│", "10", "┐", "11", "│"]
                Text { text: modelData; color: Palette.red; opacity: index % 6 === 0 ? 0.75 : 0.44; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 8 }
            }
        }
    }
    Text {
        x: inset + 10; y: root.height * 0.046
        text: "// OMARCHY     /     CYBERPUNK"
        color: Palette.cyan; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 13
    }

    Item {
        id: centre
        width: Layout.promptWidth
        height: Layout.promptHeight
        readonly property real layoutScale: Math.min(
            Layout.baseScale * root.width / Layout.referenceWidth,
            Layout.baseScale * root.height / Layout.referenceHeight,
            (root.width - 50) / Layout.promptWidth)
        scale: layoutScale
        transformOrigin: Item.TopLeft
        x: (root.width - width * layoutScale) / 2
        y: root.height / 2 + Math.min(112, root.height * 0.105) * layoutScale -
            (Layout.fieldY + Layout.fieldHeight / 2) * layoutScale
        Item {
            id: logo
            width: Layout.logoWidth
            height: width * 284 / 896
            anchors.horizontalCenter: parent.horizontalCenter
            y: -height - Layout.logoGap
            property int faultFrame: 0
            Image {
                anchors.fill: parent
                source: "logo.png"
                smooth: true
                visible: logo.faultFrame === -1
            }
            Repeater {
                model: 7
                Image {
                    width: logo.width
                    height: logo.height
                    source: "logo-fault-" + index + ".png"
                    smooth: true
                    visible: logo.faultFrame === index
                }
            }
        }
        SequentialAnimation {
            id: logoEntrance
            running: false
            loops: 1
            PauseAnimation { duration: 60 }
            ScriptAction { script: logo.faultFrame = 1 }
            PauseAnimation { duration: 40 }
            ScriptAction { script: logo.faultFrame = 2 }
            PauseAnimation { duration: 80 }
            ScriptAction { script: logo.faultFrame = 3 }
            PauseAnimation { duration: 40 }
            ScriptAction { script: logo.faultFrame = 4 }
            PauseAnimation { duration: 80 }
            ScriptAction { script: logo.faultFrame = 5 }
            PauseAnimation { duration: 60 }
            ScriptAction { script: logo.faultFrame = 6 }
            PauseAnimation { duration: 120 }
            onFinished: logo.faultFrame = -1
        }
        Rectangle { x: 0; width: 19; height: 2; color: Palette.red; opacity: 0.85 }
        Rectangle { x: 0; width: 2; height: 15; color: Palette.red; opacity: 0.85 }
        Rectangle { x: 25; width: parent.width - 50; height: 1; color: Palette.red; opacity: 0.64 }
        Rectangle { anchors.right: parent.right; width: 2; height: 15; color: Palette.red; opacity: 0.70 }
        Text {
            x: 25; y: 39; text: "// AUTHENTICATION SEQUENCE"
            color: Palette.red; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 13; font.bold: true
        }
        Text { x: 25; y: 78; text: "USER"; color: Palette.dim; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 12 }
        TextInput {
            id: userName
            x: 202; y: 72; width: 224; height: 24
            text: userModel.lastUser
            color: Palette.text; selectionColor: Palette.cyan
            horizontalAlignment: TextInput.AlignRight
            font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 12
            KeyNavigation.tab: sessionPicker
            Keys.onReturnPressed: password.forceActiveFocus()
        }
        Text {
            x: 24; y: 97
            text: root.loginFailed ? "ACCESS DENIED / RETRY" :
                (root.authenticating ? "VERIFYING IDENTITY" : "ENTER PASSWORD")
            color: root.loginFailed ? Palette.red : Palette.dim
            font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 11
        }
        Rectangle {
            id: passwordField
            x: (centre.width - width) / 2; y: Layout.fieldY
            width: Layout.fieldWidth; height: Layout.fieldHeight
            property color accent: Palette.red
            color: Qt.rgba(accent.r, accent.g, accent.b, 22 / 255)
            border.color: accent; border.width: 1
            Rectangle { width: 4; height: parent.height; color: passwordField.accent }
            Text { x: 24; anchors.verticalCenter: parent.verticalCenter; text: ">"; color: Palette.red; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 19 }
            Text {
                anchors.fill: parent; anchors.leftMargin: 56; anchors.rightMargin: 20
                visible: password.text.length === 0
                text: root.loginFailed ? "CREDENTIALS REJECTED" : "ENTER PASSWORD"
                color: root.loginFailed ? Palette.red : Palette.dim
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 18
                horizontalAlignment: Text.AlignLeft; verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            TextInput {
                id: password
                objectName: "passwordInput"
                x: 18; width: parent.width - 36; height: parent.height
                verticalAlignment: TextInput.AlignVCenter
                echoMode: TextInput.Password; passwordMaskDelay: 0; passwordCharacter: "●"
                color: "transparent"; selectionColor: "#5553e3d2"; selectedTextColor: "transparent"
                cursorDelegate: Item {}
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 18
                enabled: !root.authenticating
                KeyNavigation.tab: userName
                Keys.onReturnPressed: root.login()
                Keys.onEnterPressed: root.login()
                Keys.onEscapePressed: { password.text = ""; root.loginFailed = false }
                onTextChanged: { if (text.length > 0) root.loginFailed = false; masks.requestPaint() }
                onCursorPositionChanged: masks.requestPaint()
                onActiveFocusChanged: masks.requestPaint()
            }
            Canvas {
                id: masks
                x: 56; anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 80; height: parent.height * 0.54
                visible: password.text.length > 0
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    var count = password.text.length
                    if (!count) return
                    var step = Math.min(20, width / count)
                    var glyph = Math.min(14, step * 0.76)
                    for (var i = 0; i < count; i++) {
                        var left = i * step
                        ctx.beginPath()
                        ctx.moveTo(left + 1, 0)
                        ctx.lineTo(left + glyph, 0)
                        ctx.lineTo(left + glyph, height - 5)
                        ctx.lineTo(left + glyph - Math.min(5, glyph * 0.35), height)
                        ctx.lineTo(left + 1, height)
                        ctx.closePath()
                        ctx.fillStyle = "#32ff435b"
                        ctx.fill()
                        ctx.lineWidth = 1.4
                        ctx.strokeStyle = "#ff435b"
                        ctx.stroke()
                    }
                    if (!root.authenticating && !root.loginFailed && password.activeFocus) {
                        ctx.fillStyle = "#ff6474"
                        ctx.fillRect(Math.min(width - 2, password.cursorPosition * step + 2), 2, 2, height - 4)
                    }
                }
                MouseArea {
                    objectName: "maskMouseArea"
                    anchors.fill: parent
                    property int anchorPosition: 0
                    function positionAt(x) {
                        var count = password.text.length
                        var step = Math.min(20, masks.width / count)
                        return Math.max(0, Math.min(count, Math.round((x - 2) / step)))
                    }
                    onPressed: function(mouse) {
                        password.forceActiveFocus()
                        anchorPosition = positionAt(mouse.x)
                        password.cursorPosition = anchorPosition
                    }
                    onPositionChanged: function(mouse) {
                        if (pressed) password.select(anchorPosition, positionAt(mouse.x))
                    }
                }
            }
            Rectangle { id: scanLine; width: parent.width; height: 2; color: Palette.red; opacity: 0; z: 3 }
            SequentialAnimation {
                id: scan
                NumberAnimation { target: scanLine; property: "opacity"; from: 0; to: 0.7; duration: 65 }
                NumberAnimation { target: scanLine; property: "y"; from: 0; to: passwordField.height - 2; duration: 230 }
                NumberAnimation { target: scanLine; property: "opacity"; to: 0; duration: 90 }
            }
            // The full-height native TextInput can cover a 1px border after
            // fractional scaling; paint the lower edge above it as on Plymouth.
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width; height: 2
                color: Palette.red; z: 4
            }
        }
        Item {
            id: submit
            x: (centre.width - width) / 2; y: Layout.buttonY
            width: Layout.fieldWidth; height: Layout.buttonHeight
            activeFocusOnTab: true; enabled: !root.authenticating
            Keys.onReturnPressed: root.login()
            Keys.onEnterPressed: root.login()
            Keys.onSpacePressed: root.login()
            Canvas {
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.beginPath()
                    ctx.moveTo(22, 0.5); ctx.lineTo(width - 0.5, 0.5); ctx.lineTo(width - 0.5, height - 9)
                    ctx.lineTo(width - 9, height - 0.5); ctx.lineTo(0.5, height - 0.5)
                    ctx.lineTo(0.5, 22); ctx.closePath()
                    ctx.fillStyle = Palette.red; ctx.globalAlpha = 22 / 255; ctx.fill()
                    ctx.lineWidth = 1; ctx.strokeStyle = Palette.red; ctx.globalAlpha = 0.8; ctx.stroke()
                    ctx.globalAlpha = 1
                }
            }
            Text {
                anchors.centerIn: parent; text: "LOG IN"; color: Palette.red
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 14; font.bold: true; font.letterSpacing: 2
            }
            MouseArea { anchors.fill: parent; enabled: submit.enabled; onClicked: root.login() }
        }
        Text {
            x: (centre.width - Layout.fieldWidth) / 2; y: Layout.hintY
            visible: !root.authenticating
            text: "ESC CLEAR  /  ENTER CONFIRM"
            color: Palette.dim; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 11
        }
        Item {
            id: activity
            x: (centre.width - Layout.fieldWidth) / 2; y: Layout.hintY
            width: Layout.fieldWidth; height: 18
            visible: root.authenticating; clip: true
            Rectangle { y: 8; width: parent.width; height: 2; color: Palette.cyan; opacity: 0.25 }
            Rectangle { id: pulse; y: 6; width: 90; height: 6; color: Palette.cyan; opacity: 0.8; x: -width }
            SequentialAnimation {
                running: root.authenticating && !root.succeeded; loops: Animation.Infinite
                NumberAnimation { target: pulse; property: "x"; from: -pulse.width; to: activity.width; duration: 1050; easing.type: Easing.InOutSine }
                PauseAnimation { duration: 160 }
            }
            Rectangle { visible: root.succeeded; y: 7; width: parent.width; height: 4; color: Palette.cyan }
        }
        Item {
            id: sessionPicker
            x: (centre.width - Layout.fieldWidth) / 2; y: Layout.promptHeight - 30
            width: Layout.fieldWidth; height: 26; activeFocusOnTab: true
            Keys.onLeftPressed: root.changeSession(-1)
            Keys.onRightPressed: root.changeSession(1)
            KeyNavigation.tab: password
            Text {
                width: parent.width; text: "SESSION  <  " + root.sessionName.toUpperCase() + "  >"
                color: sessionPicker.activeFocus ? Palette.text : Palette.cyan
                font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 11; elide: Text.ElideRight
            }
            MouseArea { anchors.fill: parent; onClicked: { root.changeSession(1); sessionPicker.forceActiveFocus() } }
        }
    }
    Text {
        x: inset + 10; y: root.height * 0.92; width: root.width - 2 * inset
        text: "TAB  NEXT FIELD     /     ENTER  AUTHENTICATE     /     ESC  CLEAR PASSWORD"
        color: Palette.dim; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 8; elide: Text.ElideRight
    }
    Component.onCompleted: { password.forceActiveFocus(); scan.start(); logoEntrance.start() }
}
