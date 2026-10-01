import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Services.Polkit
import Quickshell.Wayland
import qs.Commons
import qs.Ui
import "PolkitModel.js" as PolkitModel
import "../lightqv.cyberpunk-lock" as LockArt

Item {
  id: root

  property string fontFamily: "JetBrainsMono Nerd Font"
  property color accent: Color.polkit.accent
  property color background: Color.polkit.background
  property color foreground: Color.polkit.text
  property color border: Color.polkit.border
  property color borderError: Color.polkit.borderError
  property color scrim: Color.polkit.scrim
  property bool closing: false
  property bool submitted: false
  property string currentMessage: ""
  property string currentPrompt: ""
  property string currentSupplementary: ""
  property bool responseRequired: false
  property bool responseVisible: false
  property bool failed: false
  property bool errorFlash: false
  property bool fingerprintConfigured: false
  property bool laptopClosed: false
  property int shakeOffset: 0
  property bool capturePending: false
  property bool captureReady: false
  property int captureVersion: 0
  readonly property string capturePath: Quickshell.env("XDG_RUNTIME_DIR") + "/lightqv-cyberpunk-polkit.png"
  readonly property string wallpaperPath: "file://" + Quickshell.env("HOME") + "/.local/state/omarchy/current/background"
  readonly property bool dialogVisible: polkitAgent.isActive || closing
  // Fingerprint owns the view until PAM requests a password, including when
  // the clamshell gate bypasses the inaccessible sensor.
  readonly property bool fingerprintMode: fingerprintConfigured && !laptopClosed && dialogVisible && !responseRequired && !submitted && !errorFlash

  function authorizationLabel(message) { return PolkitModel.authorizationLabel(message) }
  function loadPamConfig(raw) { fingerprintConfigured = PolkitModel.fingerprintConfiguredFromPamConfig(raw) }
  function refreshLidState() { if (!laptopClosedProc.running) laptopClosedProc.running = true }

  function resetSnapshot() {
    capturePending = false
    captureReady = false
    if (!clearCaptureProc.running) clearCaptureProc.running = true
    currentMessage = ""
    currentPrompt = ""
    currentSupplementary = ""
    responseRequired = false
    responseVisible = false
    failed = false
    errorFlash = false
    submitted = false
    passwordInput.text = ""
  }

  function syncFromFlow() {
    var flow = polkitAgent.flow
    if (!flow) return
    currentMessage = String(flow.message || "Authentication is needed...")
    currentPrompt = String(flow.inputPrompt || "")
    currentSupplementary = String(flow.supplementaryMessage || "")
    responseRequired = !!flow.isResponseRequired
    responseVisible = !!flow.responseVisible
    failed = !!flow.failed
    if (responseRequired) submitted = false
  }

  function beginFlow() {
    closeTimer.stop()
    closing = false
    captureReady = false
    capturePending = true
    captureWait.restart()
    if (!captureProc.running) captureProc.running = true
    submitted = false
    passwordInput.text = ""
    refreshLidState()
    syncFromFlow()
    scanAnimation.restart()
    Qt.callLater(refocus)
  }

  function refocus() {
    if (!dialogVisible || capturePending) return
    if (fingerprintMode) keyCatcher.forceActiveFocus()
    else passwordInput.forceActiveFocus()
  }

  function submitResponse() {
    var flow = polkitAgent.flow
    if (!flow || !flow.isResponseRequired) return
    submitted = true
    errorFlash = false
    flow.submit(passwordInput.text)
    passwordInput.text = ""
    keyCatcher.forceActiveFocus()
  }

  function cancelRequest() {
    var flow = polkitAgent.flow
    passwordInput.text = ""
    submitted = false
    closing = true
    closeTimer.restart()
    if (flow) flow.cancelAuthenticationRequest()
  }

  function triggerFailureFeedback() {
    submitted = false
    errorFlash = true
    passwordInput.text = ""
    errorTimer.restart()
    shakeAnimation.restart()
    scanAnimation.restart()
    Qt.callLater(refocus)
  }

  Timer {
    id: closeTimer
    interval: 300
    onTriggered: { closing = false; resetSnapshot() }
  }
  Timer {
    id: errorTimer
    interval: 1200
    onTriggered: root.errorFlash = false
  }
  Timer {
    id: captureWait
    interval: 850
    onTriggered: { root.capturePending = false; root.refocus() }
  }
  Process {
    id: captureProc
    command: [Quickshell.env("HOME") + "/.config/omarchy/plugins/lightqv.cyberpunk-polkit/capture-auth", root.capturePath]
    onExited: function(code) {
      root.captureReady = code === 0 && root.dialogVisible
      root.captureVersion += 1
      root.capturePending = false
      captureWait.stop()
      root.refocus()
    }
  }
  Process {
    id: clearCaptureProc
    command: ["rm", "-f", "--", root.capturePath]
  }
  LockArt.SignalRhythm {
    id: rhythm
    repeatWhileVisible: root.dialogVisible && !root.capturePending
    reducedMotion: Quickshell.env("OMARCHY_REDUCED_MOTION") === "1"
  }
  SequentialAnimation {
    id: shakeAnimation
    NumberAnimation { target: root; property: "shakeOffset"; to: -8; duration: 35; easing.type: Easing.OutQuad }
    NumberAnimation { target: root; property: "shakeOffset"; to: 8; duration: 50; easing.type: Easing.InOutQuad }
    NumberAnimation { target: root; property: "shakeOffset"; to: 0; duration: 55; easing.type: Easing.OutQuad }
  }
  SequentialAnimation {
    id: scanAnimation
    NumberAnimation { target: scanLine; property: "opacity"; from: 0; to: 0.75; duration: 65 }
    NumberAnimation { target: scanLine; property: "y"; from: inputField.y - 10; to: inputField.y + inputField.height + 10; duration: 230 }
    NumberAnimation { target: scanLine; property: "opacity"; to: 0; duration: 90 }
  }
  FileView {
    path: "/etc/pam.d/polkit-1"
    watchChanges: true
    printErrors: false
    onLoaded: root.loadPamConfig(text())
    onLoadFailed: root.fingerprintConfigured = false
    onFileChanged: reload()
  }
  Process {
    id: laptopClosedProc
    command: ["bash", "-c", "omarchy-hw-laptop-closed && echo closed || echo open"]
    stdout: StdioCollector { id: laptopClosedOut; waitForEnd: true }
    onExited: root.laptopClosed = String(laptopClosedOut.text || "").trim() === "closed"
  }

  PolkitAgent {
    id: polkitAgent
    path: "/org/omarchy/PolkitAgent"
    onAuthenticationRequestStarted: root.beginFlow()
    onIsActiveChanged: {
      if (isActive) root.syncFromFlow()
      else if (!root.closing) root.resetSnapshot()
    }
    onIsRegisteredChanged: {
      if (isRegistered) console.log("omarchy polkit agent registered")
      else console.warn("omarchy polkit agent is not registered; another agent may be running")
    }
  }
  Connections {
    target: polkitAgent.flow
    function onIsResponseRequiredChanged() {
      root.syncFromFlow()
      if (!polkitAgent.flow || !polkitAgent.flow.isResponseRequired) passwordInput.text = ""
      Qt.callLater(root.refocus)
    }
    function onInputPromptChanged() { root.syncFromFlow() }
    function onResponseVisibleChanged() { root.syncFromFlow() }
    function onSupplementaryMessageChanged() { root.syncFromFlow() }
    function onFailedChanged() { root.syncFromFlow() }
    function onAuthenticationFailed() { root.syncFromFlow(); root.triggerFailureFeedback() }
    function onAuthenticationSucceeded() { root.closing = true; closeTimer.restart() }
    function onAuthenticationRequestCancelled() { root.closing = true; closeTimer.restart() }
  }

  PanelWindow {
    id: panel
    visible: root.dialogVisible && !root.capturePending
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-polkit"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore

    Image {
      id: backdrop
      anchors.fill: parent
      source: root.captureReady ? "file://" + root.capturePath + "?v=" + root.captureVersion : root.wallpaperPath
      fillMode: Image.PreserveAspectCrop
      asynchronous: true
      cache: false
    }
    MultiEffect {
      anchors.fill: backdrop
      source: backdrop
      autoPaddingEnabled: false
      blurEnabled: backdrop.status === Image.Ready
      blur: 0.22
      blurMax: 48
      blurMultiplier: 1.0
      contrast: -0.02
    }
    Rectangle { anchors.fill: parent; color: root.scrim }
    LockArt.SignalFault {
      anchors.fill: parent
      imageSource: backdrop.source
      phase: rhythm.phase
      strength: rhythm.intensity
      variant: rhythm.variant
      red: root.accent
      cyan: root.border
    }
    MouseArea { anchors.fill: parent; onClicked: root.refocus() }

    LockArt.LockHud {
      id: hud
      anchors.fill: parent
      fieldWidth: Math.min(381, panel.width * 0.8)
      fieldHeight: 54
      fieldYOffset: Math.min(112, panel.height * 0.105)
      red: root.accent
      cyan: root.border
      textColor: root.foreground
      mutedColor: Util.alpha(root.foreground, 0.55)
      fontFamily: root.fontFamily
      userLabel: Quickshell.env("USER") || "LOCAL USER"
      topLeftLabel: "//  LOCAL  /  PRIVILEGED ACCESS"
      topRightLabel: "AUTHORIZATION REQUIRED"
      showClock: false
      submitLabel: "SUBMIT"
      hintLabel: "ESC ABORT  /  ENTER CONFIRM"
      fingerprintMode: root.fingerprintMode
      fingerprintAvailable: root.fingerprintConfigured
      authenticating: root.submitted
      failed: root.errorFlash
      signalPulse: rhythm.intensity
      onLoginRequested: if (root.responseRequired && !root.submitted && !root.fingerprintMode) root.submitResponse()
    }
    Text {
      x: (parent.width - hud.fieldWidth) / 2
      y: hud.fieldCenter - hud.fieldHeight / 2 - 128
      width: hud.fieldWidth
      text: root.authorizationLabel(root.currentMessage)
      textFormat: Text.PlainText
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: 11
      elide: Text.ElideRight
      opacity: 0.8
    }
    Item {
      id: keyCatcher
      anchors.fill: parent
      focus: true
      Keys.priority: Keys.BeforeItem
      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Escape) {
          root.cancelRequest()
          event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
          if (root.responseRequired && !root.fingerprintMode) root.submitResponse()
          event.accepted = true
        }
      }
    }
    OpticalGlyph {
      anchors.horizontalCenter: parent.horizontalCenter
      y: hud.fieldCenter - height / 2
      width: Math.round(hud.fieldHeight * 0.8)
      height: width
      visible: root.fingerprintMode
      text: "󰈷"
      fontFamily: root.fontFamily
      fontSize: Math.round(hud.fieldHeight * 0.8)
      color: root.errorFlash ? Color.polkit.textError : root.accent
    }
    Rectangle {
      id: inputField
      width: hud.fieldWidth
      height: hud.fieldHeight
      anchors.centerIn: parent
      anchors.verticalCenterOffset: hud.fieldYOffset
      anchors.horizontalCenterOffset: root.shakeOffset
      visible: !root.fingerprintMode
      color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 22 / 255)
      border.color: root.errorFlash ? root.borderError : root.accent
      border.width: 1
      clip: true
      Rectangle { width: 4; height: parent.height; color: root.accent }
      Text {
        x: 24
        anchors.verticalCenter: parent.verticalCenter
        text: ">"
        color: root.accent
        font.family: root.fontFamily
        font.pixelSize: 19
      }
      TextInput {
        id: passwordInput
        anchors.fill: parent
        anchors.leftMargin: 56
        anchors.rightMargin: 20
        verticalAlignment: TextInput.AlignVCenter
        activeFocusOnPress: true
        clip: true
        echoMode: root.responseVisible ? TextInput.Normal : TextInput.Password
        passwordMaskDelay: 0
        color: root.responseVisible ? root.foreground : "transparent"
        selectionColor: root.responseVisible ? Util.alpha(root.border, 0.45) : "transparent"
        selectedTextColor: root.responseVisible ? root.foreground : "transparent"
        font.family: root.fontFamily
        font.pixelSize: 18
        // Qt can change cursorVisible when focus changes. An empty delegate
        // guarantees that masked mode cannot paint a second native caret.
        cursorDelegate: Item {}
        readOnly: root.submitted || root.errorFlash
        enabled: root.dialogVisible
        onAccepted: root.submitResponse()
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) { root.cancelRequest(); event.accepted = true }
        }
      }
      Text {
        anchors.left: parent.left
        anchors.leftMargin: 56
        anchors.right: parent.right
        anchors.rightMargin: 56
        horizontalAlignment: Text.AlignHCenter
        anchors.verticalCenter: parent.verticalCenter
        text: root.errorFlash ? "ACCESS DENIED" : (root.submitted ? "VERIFYING..." : "ENTER PASSWORD")
        visible: passwordInput.text.length === 0
        color: root.errorFlash ? root.borderError : root.foreground
        opacity: root.errorFlash ? 1 : 0.50
        font.family: root.fontFamily
        font.pixelSize: 18
      }
      LockArt.PasswordSlots {
        anchors.fill: parent
        input: passwordInput
        accent: root.accent
        selectionColor: Util.alpha(root.border, 0.45)
        caretEnabled: !root.submitted && !root.errorFlash
        visible: !root.responseVisible
      }
      Rectangle {
        x: passwordInput.x + passwordInput.cursorRectangle.x
        y: passwordInput.y + passwordInput.cursorRectangle.y
        width: 2; height: passwordInput.cursorRectangle.height
        color: root.accent
        visible: root.responseVisible && passwordInput.activeFocus && !root.submitted && !root.errorFlash
      }
    }
    Rectangle {
      id: scanLine
      x: inputField.x
      width: inputField.width
      height: 2
      color: root.accent
      opacity: 0
      z: 4
    }
  }
}
