import QtQuick
import "../../lock-plugin" as LockArt

Rectangle {
    width: 381; height: 54
    color: "#1b1118"
    TextInput {
        id: input
        objectName: "testInput"
        anchors.fill: parent
        focus: true
        color: "transparent"
        selectionColor: "transparent"
        echoMode: TextInput.Password
        cursorDelegate: Item {}
    }
    LockArt.PasswordSlots {
        objectName: "testSlots"
        anchors.fill: parent
        input: input
    }
}
