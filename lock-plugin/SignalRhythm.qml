import QtQuick

// Four beats: fast / slow / slow / fast. A fresh variant remaps which screen
// regions respond on each appearance without changing the readable cadence.
Item {
    id: rhythm
    property real phase: 0
    property int variant: 0
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
        variant = (variant + 1 + Math.floor(Math.random() * 3)) % 4
        sweep.restart()
    }

    NumberAnimation {
        id: sweep
        target: rhythm
        property: "phase"
        from: 0
        to: 1
        duration: 760
    }
}
