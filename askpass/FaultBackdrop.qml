import QtQuick
import QtQuick.Effects
import "../lock-plugin" as LockArt

// The actual Polkit effect, over the askpass's in-memory frozen image.
Rectangle {
    id: root
    property real phase: 1
    property int variant: 0
    property color red: "#ff3045"
    property color cyan: "#53e3d2"
    property color background: "#07090e"
    color: background
    Image {
        id: backdrop
        anchors.fill: parent
        source: "image://askpass/frozen"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
    }
    MultiEffect {
        anchors.fill: backdrop
        source: backdrop
        autoPaddingEnabled: false
        blurEnabled: backdrop.status === Image.Ready
        blur: .22; blurMax: 48; blurMultiplier: 1
        contrast: -.02
    }
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(root.background.r, root.background.g, root.background.b, 170 / 255)
    }
    LockArt.SignalRhythm { id: envelope; phase: root.phase }
    LockArt.SignalFault {
        anchors.fill: parent
        imageSource: "image://askpass/frozen"
        // Python image providers must stay on the UI thread in QQuickWidget.
        asynchronousImages: false
        phase: root.phase
        strength: envelope.intensity
        variant: root.variant
        red: root.red
        cyan: root.cyan
    }
    LockArt.CurvedLabel {
        x: Math.max(18, root.width * .023)
        y: Math.max(18, root.height * .032)
        text: "//  LOCAL  /  PRIVILEGED ACCESS"
        color: root.red
    }
    LockArt.CurvedLabel {
        anchors.right: parent.right
        anchors.rightMargin: Math.max(25, root.width * .031)
        y: Math.max(18, root.height * .029)
        text: "AUTHORIZATION REQUIRED"
        color: root.red; rightSide: true
    }
}
