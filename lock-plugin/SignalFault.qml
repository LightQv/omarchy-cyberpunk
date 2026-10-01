import QtQuick

// Frozen-backdrop-only displacement. Never samples a live unlocked surface.
Item {
    id: fault
    property url imageSource: ""
    property real strength: 0
    property real phase: 0
    property int variant: 0
    property bool asynchronousImages: true
    property color red: "#ff3045"
    property color cyan: "#53e3d2"

    visible: strength > 0.015 && imageSource.toString().length > 0
    enabled: false

    Repeater {
        // Independent envelopes scatter strips and square patches across the
        // frozen backdrop. The password field (~58% down) stays unobscured.
        model: [
            { x: 0.04, y: 0.17, width: 0.32, height: 8, shift: 19, beat: 0, offset: 0.04, life: 0.87 },
            { x: 0.55, y: 0.24, width: 0.40, height: 9, shift: -27, beat: 1, offset: 0.05, life: 0.80 },
            { x: 0.16, y: 0.38, width: 0.55, height: 7, shift: 31, beat: 2, offset: 0.02, life: 0.90 },
            { x: 0.51, y: 0.49, width: 0.40, height: 11, shift: -22, beat: 1, offset: 0.17, life: 0.68 },
            { x: 0.05, y: 0.67, width: 0.36, height: 6, shift: 25, beat: 3, offset: 0.08, life: 0.80 },
            { x: 0.35, y: 0.76, width: 0.57, height: 10, shift: -24, beat: 2, offset: 0.15, life: 0.72 },
            { x: 0.03, y: 0.87, width: 0.30, height: 7, shift: 17, beat: 3, offset: 0.22, life: 0.71 },
            { x: 0.73, y: 0.82, width: 0.23, height: 5, shift: -14, beat: 0, offset: 0.15, life: 0.76 },
            { x: 0.11, y: 0.27, square: true, height: 34, shift: -22, beat: 0, offset: 0.12, life: 0.72 },
            { x: 0.30, y: 0.13, square: true, height: 42, shift: 29, beat: 2, offset: 0.04, life: 0.75 },
            { x: 0.06, y: 0.46, square: true, height: 30, shift: 18, beat: 1, offset: 0.13, life: 0.82 },
            { x: 0.88, y: 0.69, square: true, height: 28, shift: -26, beat: 3, offset: 0.08, life: 0.79 },
            { x: 0.19, y: 0.79, square: true, height: 40, shift: 27, beat: 2, offset: 0.19, life: 0.70 },
            { x: 0.69, y: 0.91, square: true, height: 26, shift: -20, beat: 3, offset: 0.02, life: 0.78 },
            { x: 0.60, y: 0.12, width: 0.17, height: 4, shift: 13, beat: 0, offset: 0.21, life: 0.62 },
            { x: 0.41, y: 0.32, square: true, height: 18, shift: -12, beat: 1, offset: 0.24, life: 0.67 },
            { x: 0.79, y: 0.42, width: 0.16, height: 4, shift: -18, beat: 2, offset: 0.18, life: 0.63 },
            { x: 0.08, y: 0.73, square: true, height: 16, shift: 15, beat: 3, offset: 0.15, life: 0.66 },
            { x: 0.56, y: 0.94, width: 0.15, height: 4, shift: -11, beat: 3, offset: 0.27, life: 0.60 }
        ]
        Item {
            id: band
            x: fault.width * modelData.x
            y: fault.height * modelData.y
            width: modelData.square ? modelData.height : fault.width * modelData.width
            height: modelData.height
            clip: true
            readonly property int beat: (modelData.beat + fault.variant) % 4
            readonly property real beatStart: [0, 0.19, 0.50, 0.83][beat]
            readonly property real beatLength: [0.13, 0.24, 0.26, 0.13][beat]
            readonly property real localTime: (fault.phase - beatStart - modelData.offset * beatLength) / (modelData.life * beatLength)
            readonly property real attack: Math.max(0, Math.min(1, localTime / 0.18))
            readonly property real release: Math.max(0, Math.min(1, (1 - localTime) / 0.28))
            readonly property real level: fault.strength * Math.min(attack, release)
            readonly property bool inverted: (index + fault.variant) % 2 === 1
            visible: level > 0.02
            // Make negative fragments nearly opaque at peak: half-opacity
            // inversion over the source cancels chroma into washed-out grey.
            opacity: inverted ? Math.min(1, level * 4) : level

            Image {
                id: stripImage
                x: -band.x + modelData.shift * band.level * (0.6 + 0.4 * Math.sin(band.localTime * Math.PI * 3 + index))
                y: -band.y
                width: fault.width
                height: fault.height
                source: fault.imageSource
                fillMode: Image.PreserveAspectCrop
                asynchronous: fault.asynchronousImages
                cache: true
                sourceSize.width: fault.width
                sourceSize.height: fault.height
            }
            ShaderEffect {
                x: stripImage.x
                y: stripImage.y
                width: stripImage.width
                height: stripImage.height
                property variant source: stripImage
                property color redTint: fault.red
                fragmentShader: "negative.frag.qsb"
                visible: band.inverted
            }
            Rectangle {
                anchors.fill: parent
                color: fault.red
                opacity: band.inverted ? 0.03 : 0.22
            }
            Rectangle {
                x: index % 2 === 0 ? 0 : band.width * 0.27
                width: band.width * (modelData.square ? 1 : (index % 3 === 1 ? 0.32 : 0.58))
                height: 1
                color: index % 3 === 1 ? fault.cyan : fault.red
                opacity: 0.72
            }
            Rectangle {
                x: band.width * (index % 3 === 2 ? 0.22 : 0.62)
                y: band.height - 1
                width: band.width * 0.19
                height: 1
                color: fault.cyan
                opacity: 0.55
            }
        }
    }
}
