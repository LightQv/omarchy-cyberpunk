import QtQuick
import "../../lock-plugin" as LockArt

Item {
    width: 100; height: 100
    LockArt.SignalRhythm {
        objectName: "testRhythm"
        repeatWhileVisible: true
    }
}
