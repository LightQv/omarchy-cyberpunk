import QtQuick
import qs.Commons

// Visual clock only: the service still owns expiry, close reasons and delivery.
Item {
  id: motion
  property bool animated: true
  property bool leaving: false
  property bool interactive: false
  readonly property bool reducedMotion: Style.duration(1) === 0
  property real revealFraction: 1
  property real symbolOpacity: 1
  readonly property bool entering: intro.running
  readonly property bool exiting: outro.running
  property bool ready: false

  function settle() {
    intro.stop()
    outro.stop()
    revealFraction = leaving ? 0 : 1
    symbolOpacity = leaving ? 0 : 1
  }
  function enter() {
    settle()
    if (!animated || reducedMotion || interactive || leaving) return
    revealFraction = 0
    symbolOpacity = 1
    intro.start()
  }
  onLeavingChanged: {
    intro.stop()
    outro.stop()
    if (leaving && animated && !reducedMotion) outro.start()
    else settle()
  }
  onInteractiveChanged: if (interactive && !leaving) settle()
  onReducedMotionChanged: if (reducedMotion) settle()
  onAnimatedChanged: if (ready) {
    if (animated) enter()
    else settle()
  }
  Component.onCompleted: { ready = true; enter() }

  SequentialAnimation {
    id: intro
    NumberAnimation { target: motion; property: "symbolOpacity"; from: 1; to: 0.15; duration: Style.duration(220) }
    NumberAnimation { target: motion; property: "symbolOpacity"; from: 0.15; to: 1; duration: Style.duration(220) }
    NumberAnimation { target: motion; property: "symbolOpacity"; from: 1; to: 0.15; duration: Style.duration(220) }
    NumberAnimation { target: motion; property: "symbolOpacity"; from: 0.15; to: 1; duration: Style.duration(220) }
    ParallelAnimation {
      SequentialAnimation {
        NumberAnimation { target: motion; property: "symbolOpacity"; from: 1; to: 0.15; duration: Style.duration(220) }
        NumberAnimation { target: motion; property: "symbolOpacity"; from: 0.15; to: 1; duration: Style.duration(220) }
      }
      NumberAnimation { target: motion; property: "revealFraction"; from: 0; to: 1; duration: Style.duration(550); easing.type: Easing.OutCubic }
    }
  }
  SequentialAnimation {
    id: outro
    NumberAnimation { target: motion; property: "revealFraction"; to: 0; duration: Style.duration(360); easing.type: Easing.OutCubic }
    NumberAnimation { target: motion; property: "symbolOpacity"; to: 0; duration: Style.duration(160) }
  }
}
