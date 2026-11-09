import QtQuick
import Quickshell
import qs.Commons
import qs.Commons as Commons

// Keep Omarchy's password/fingerprint field, focus and secure surface intact.
// The decorative HUD is shared with the standalone, non-authenticating preview.
StockLockView {
    id: root

    function pulseSignal() {
        if (inputEnabled) rhythm.play()
    }

    SignalRhythm {
        id: rhythm
        onPhaseChanged: root.signalPhase = phase
        onIntensityChanged: root.signalPulse = intensity
        onVariantChanged: root.signalVariant = variant
    }

    function submitFromButton() {
        if (!inputEnabled || authenticatingPassword || !passwordText.length) return
        var submitted = passwordText
        passwordTextEdited("")
        submitPassword(submitted)
    }

    LockHud {
        id: hud
        anchors.fill: parent
        fieldWidth: root.fieldWidth
        fieldHeight: root.fieldHeight
        fieldYOffset: root.fieldYOffset
        red: Commons.Color.lock.borderActive
        cyan: Commons.Color.lock.border
        textColor: Commons.Color.lock.text
        mutedColor: Commons.Color.lock.placeholder
        failed: root.failureMessage.length > 0
        authenticating: root.authenticatingPassword
        canSubmit: root.passwordText.length > 0
        fingerprintAvailable: root.fingerprintConfigured
        fontFamily: Style.font.family
        userLabel: Quickshell.env("USER") || "LOCAL USER"
        signalPulse: root.signalPulse
        onLoginRequested: root.submitFromButton()
    }

    onInputEnabledChanged: if (inputEnabled) { hud.scan(); pulseSignal() }
    onAuthenticatingPasswordChanged: if (authenticatingPassword) pulseSignal()
    onFailureMessageChanged: if (failureMessage.length > 0) pulseSignal()
    Component.onCompleted: if (inputEnabled) { hud.scan(); pulseSignal() }
}
