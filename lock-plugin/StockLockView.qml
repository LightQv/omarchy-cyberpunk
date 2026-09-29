// Pinned Omarchy LockView with a Cyberpunk backdrop scrim; see scripts/build-lock.
import QtQuick
import QtQuick.Effects
import qs.Commons
import qs.Ui

Item {
  id: root

  property string backgroundPath: ""
  property int backgroundVersion: 0
  property bool fingerprintConfigured: false
  property bool authenticatingPassword: false
  property string failureMessage: ""
  property int failedAttempts: 0
  property bool inputEnabled: true
  property bool loadBackground: true
  property string passwordText: ""
  property real signalPulse: 0
  property real signalPhase: 0
  property int signalVariant: 0
  property bool syncingPasswordText: false

  readonly property string placeholderText: "ENTER PASSWORD"
  readonly property int fieldWidth: 381
  readonly property int fieldHeight: 54
  readonly property real fieldYOffset: Math.min(112, height * 0.105)
  readonly property int outlineThickness: 1
  readonly property int fieldFontSize: Math.round(Style.font.heading * 0.85)
  readonly property int passwordDotFontSize: Math.round(Style.font.heading * 1.33)
  readonly property int passwordDotLetterSpacing: Math.round(Style.font.heading * 0.19)
  // Space to keep clear on each side of the field for the fingerprint icon
  // (icon width plus a gap) so the centered dots never run under it.
  readonly property real fingerprintReserve: fingerprintConfigured ? Math.round(fingerprintIcon.implicitWidth + 12) : 0
  // Shrink the dots to fit once the password outgrows the field, so every
  // keystroke stays visible — otherwise long passwords clip with no feedback.
  readonly property real passwordDotScale: dotMetrics.advanceWidth > 0
    ? Math.min(1, (passwordInput.width - 4) / dotMetrics.advanceWidth)
    : 1
  readonly property bool showPasswordCursor: inputEnabled && !authenticatingPassword && failureMessage.length === 0
  readonly property bool errorState: failureMessage.length > 0
  readonly property var inputBorderSpec: errorState
    ? Border.surfaceSpec("lock", "border-error", Color.lock.borderError, root.outlineThickness, "border-alpha")
    : Border.surfaceSpec("lock", "border-active", Color.lock.borderActive, root.outlineThickness, "border-alpha")

  signal submitPassword(string password)
  signal passwordTextEdited(string password)
  signal clearFailureRequested()
  signal wakeRequested()

  // Cache-busts the lock background by appending `?v=`. Adding a query
  // string keeps Image's loader happy while forcing it to reload when the
  // user picks a new background mid-session.
  function fileUrl(path) {
    if (!path) return ""
    var encoded = String(path).split("/").map(encodeURIComponent).join("/")
    return "file://" + encoded + "?v=" + backgroundVersion
  }

  function forcePasswordFocus() {
    passwordInput.forceActiveFocus()
  }

  function clearPassword() {
    passwordTextEdited("")
  }

  function syncPasswordText() {
    if (passwordInput.text === passwordText) return
    syncingPasswordText = true
    passwordInput.text = passwordText
    syncingPasswordText = false
  }

  onPasswordTextChanged: { syncPasswordText(); maskGlyphs.requestPaint() }
  onShowPasswordCursorChanged: maskGlyphs.requestPaint()
  onInputEnabledChanged: {
    if (inputEnabled) Qt.callLater(forcePasswordFocus)
  }
  Component.onCompleted: {
    syncPasswordText()
    if (inputEnabled) Qt.callLater(forcePasswordFocus)
  }

  // Measures the masked password at full size; passwordDotScale compares this
  // against the field width to decide how far the dots must shrink to fit.
  TextMetrics {
    id: dotMetrics
    font.family: Style.font.family
    font.pixelSize: root.passwordDotFontSize
    font.letterSpacing: root.passwordDotLetterSpacing
    text: "●".repeat(passwordInput.text.length)
  }

  Rectangle {
    anchors.fill: parent
    color: Color.background

    Image {
      id: wallpaper
      anchors.fill: parent
      source: root.loadBackground ? root.fileUrl(root.backgroundPath) : ""
      fillMode: Image.PreserveAspectCrop
      asynchronous: true
      cache: false
      sourceSize.width: width
      sourceSize.height: height
    }

    MultiEffect {
      anchors.fill: wallpaper
      source: wallpaper
      autoPaddingEnabled: false
      blurEnabled: root.loadBackground && wallpaper.status === Image.Ready
      blur: 0.22
      blurMax: 48
      blurMultiplier: 1.0
      contrast: -0.02
    }

    Rectangle {
      anchors.fill: parent
      color: Qt.rgba(Color.background.r, Color.background.g, Color.background.b, 0.09)
    }

    SignalFault {
      anchors.fill: parent
      imageSource: wallpaper.source
      strength: root.signalPulse
      phase: root.signalPhase
      variant: root.signalVariant
      red: Color.lock.borderActive
      cyan: Color.lock.border
    }

    MouseArea {
      anchors.fill: parent
      hoverEnabled: true
      onClicked: { root.wakeRequested(); root.forcePasswordFocus() }
      onPositionChanged: root.wakeRequested()
    }

    BorderSurface {
      id: inputField
      width: root.fieldWidth
      height: root.fieldHeight
      anchors.centerIn: parent
      anchors.verticalCenterOffset: root.fieldYOffset
      color: "transparent"
      borderSpec: Border.none()
      radius: 0
      clip: true

      Rectangle {
         id: inputFrame
         anchors.fill: parent
         color: Qt.rgba(Color.lock.borderActive.r, Color.lock.borderActive.g,
                        Color.lock.borderActive.b, 22 / 255)
         border.color: root.errorState ? Color.lock.borderError : Color.lock.borderActive
         border.width: 1
         Rectangle { width: 4; height: parent.height; color: inputFrame.border.color }
       }
      Text {
        x: 24
        anchors.verticalCenter: parent.verticalCenter
        text: ">"
        color: Color.lock.borderActive
        font.family: Style.font.family
        font.pixelSize: 19
      }

      TextInput {
        id: passwordInput
        anchors.fill: parent
        anchors.topMargin: inputField.borderTop
        // Reserve the fingerprint icon's width on both sides so the centered
        // dots stay symmetric and never slide under the icon as they grow.
        anchors.rightMargin: inputField.borderRight + 18 + root.fingerprintReserve
        anchors.bottomMargin: inputField.borderBottom
        anchors.leftMargin: inputField.borderLeft + 18 + root.fingerprintReserve
        verticalAlignment: TextInput.AlignVCenter
        horizontalAlignment: TextInput.AlignLeft
        activeFocusOnPress: true
        clip: true
        enabled: root.inputEnabled && !root.authenticatingPassword
        readOnly: root.authenticatingPassword
        echoMode: TextInput.Password
        passwordCharacter: "\u25CF"
        passwordMaskDelay: 0
        color: "transparent"
        selectionColor: Color.lock.selection
        selectedTextColor: "transparent"
        font.family: Style.font.family
        font.pixelSize: text.length > 0 ? Math.max(1, Math.floor(root.passwordDotFontSize * root.passwordDotScale)) : root.fieldFontSize
        font.letterSpacing: text.length > 0 ? root.passwordDotLetterSpacing * root.passwordDotScale : 0
        cursorVisible: false // The custom masks paint the visible caret.
        cursorDelegate: Rectangle {
          width: 2
          color: Color.lock.text
          visible: passwordInput.cursorVisible
        }

        onCursorPositionChanged: maskGlyphs.requestPaint()
        onActiveFocusChanged: maskGlyphs.requestPaint()

        onTextChanged: {
          if (!root.syncingPasswordText) root.passwordTextEdited(text)
          if (text.length > 0) {
            root.wakeRequested()
          }
          if (text.length > 0 && root.failureMessage.length > 0) root.clearFailureRequested()
        }

        onAccepted: {
          var submitted = root.passwordText
          root.passwordTextEdited("")
          if (submitted.length > 0) root.submitPassword(submitted)
        }

        Keys.onPressed: function(event) {
          root.wakeRequested()
          if (event.key === Qt.Key_Escape || (event.modifiers & Qt.ControlModifier && event.key === Qt.Key_U)) {
            root.passwordTextEdited("")
            event.accepted = true
          }
        }
      }

      Text {
        textFormat: Text.PlainText
        anchors.fill: inputField
        anchors.leftMargin: 56
        anchors.rightMargin: 20 + root.fingerprintReserve
        text: root.authenticatingPassword ? "Checking…" : (root.failureMessage.length > 0 ? root.failureMessage : root.placeholderText)
        visible: passwordInput.text.length === 0
        color: root.authenticatingPassword ? Color.lock.text : (root.failureMessage.length > 0 ? Color.lock.textError : Color.lock.placeholder)
        font.family: Style.font.family
        font.pixelSize: root.fieldFontSize
        font.italic: !root.authenticatingPassword && root.failureMessage.length > 0
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
      }

      // The stock TextInput still owns focus, selection and Password echo mode.
      // Both the mask count and caret position follow the real input.
      Canvas {
        id: maskGlyphs
         anchors.left: parent.left
         anchors.leftMargin: 56
         anchors.verticalCenter: parent.verticalCenter
         width: parent.width - 80 - root.fingerprintReserve
        height: parent.height * 0.54
        visible: root.passwordText.length > 0
         onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
          var ctx = getContext("2d")
          ctx.clearRect(0, 0, width, height)
          var count = root.passwordText.length
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
           if (root.showPasswordCursor) {
             ctx.fillStyle = "#ff6474"
              ctx.fillRect(Math.min(width - 2, passwordInput.cursorPosition * step + 2), 2, 2, height - 4)
            }
         }
         MouseArea {
           anchors.fill: parent
           property int anchorPosition: 0
           function positionAt(x) {
             var count = passwordInput.text.length
             var step = Math.min(20, maskGlyphs.width / count)
             return Math.max(0, Math.min(count, Math.round((x - 2) / step)))
           }
           onPressed: function(mouse) {
             passwordInput.forceActiveFocus()
             anchorPosition = positionAt(mouse.x)
             passwordInput.cursorPosition = anchorPosition
           }
           onPositionChanged: function(mouse) {
             if (pressed) passwordInput.select(anchorPosition, positionAt(mouse.x))
           }
         }
       }

      Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: inputFrame.border.color
        z: 4
      }

      // Fingerprint hint pinned inside the field's right edge when a sensor is
      // enrolled, so the user knows they can touch to unlock instead of typing.
      // Matches hyprlock, which draws its fingerprint icon in the same spot.
      Text {
        id: fingerprintIcon
        objectName: "fingerprintIndicator"
        anchors.right: parent.right
        anchors.rightMargin: inputField.borderRight + 18
        anchors.verticalCenter: parent.verticalCenter
        visible: root.fingerprintConfigured
        text: "󰈷"
        color: Color.lock.placeholder
        font.family: Style.font.family
        font.pixelSize: Math.round(root.fieldFontSize * 1.1)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
      }
    }
  }
}
