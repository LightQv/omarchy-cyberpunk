import QtQuick

// Four beats: fast / slow / slow / fast. A fresh variant remaps which screen
// regions respond on each appearance without changing the readable cadence.
Item {
    id: rhythm
    property real phase: 0
    property int variant: 0
    property bool repeatWhileVisible: false
    property bool reducedMotion: false
    property int sequenceDuration: 760
    property var speedBag: []
    property int lastSpeed: -1
    property int sequencesStarted: 0
    readonly property var sequenceSpeeds: [850, 1100, 1400]
    onRepeatWhileVisibleChanged: {
        if (repeatWhileVisible) Qt.callLater(syncMotion)
        else syncMotion()
    }
    onReducedMotionChanged: if (reducedMotion || repeatWhileVisible) Qt.callLater(syncMotion)
    Component.onCompleted: if (repeatWhileVisible) syncMotion()
    readonly property var starts: [0.0, 0.19, 0.50, 0.83]
    readonly property var lengths: [0.13, 0.24, 0.26, 0.13]
    readonly property real intensity: {
        var peak = 0
        for (var i = 0; i < 4; ++i) {
            var t = (phase - starts[i]) / lengths[i]
            if (t <= 0 || t >= 1) continue
            var rise = Math.min(1, t / (i === 0 || i === 3 ? 0.22 : 0.13))
            var fall = Math.min(1, (1 - t) / (i === 0 || i === 3 ? 0.23 : 0.18))
            peak = Math.max(peak, Math.min(rise, fall) * (i === 0 || i === 3 ? 0.95 : 0.72))
        }
        return peak
    }

    function play() {
        if (reducedMotion || repeatWhileVisible) return
        sequenceDuration = 760
        variant = (variant + 1 + Math.floor(Math.random() * 3)) % 4
        sweep.restart()
    }

    function syncMotion() {
        if (!repeatWhileVisible || reducedMotion) {
            betweenSequences.stop()
            sweep.stop()
            phase = 1
        } else if (!sweep.running && !betweenSequences.running) startSequence()
    }

    function startSequence() {
        if (!repeatWhileVisible || reducedMotion) return
        var bag = speedBag.length ? speedBag.slice() : [0, 1, 2]
        var choices = []
        for (var i = 0; i < bag.length; ++i) {
            if (bag[i] !== lastSpeed) choices.push(i)
        }
        var at = choices[Math.floor(Math.random() * choices.length)]
        lastSpeed = bag.splice(at, 1)[0]
        speedBag = bag
        sequenceDuration = sequenceSpeeds[lastSpeed]
        variant = (variant + 1 + Math.floor(Math.random() * 3)) % 4
        sequencesStarted += 1
        sweep.restart()
    }

    Timer {
        id: betweenSequences
        interval: 180
        onTriggered: rhythm.startSequence()
    }

    NumberAnimation {
        id: sweep
        target: rhythm
        property: "phase"
        from: 0
        to: 1
        duration: rhythm.sequenceDuration
        onFinished: {
            if (rhythm.repeatWhileVisible && !rhythm.reducedMotion) {
                betweenSequences.interval = 350 + Math.floor(Math.random() * 451)
                betweenSequences.start()
            }
        }
        onStopped: rhythm.phase = 1
    }
}
