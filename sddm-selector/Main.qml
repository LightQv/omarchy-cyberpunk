import QtQuick 2.15
import Qt.labs.settings 1.1
import SddmComponents 2.0

Item {
    id: root
    width: 1280
    height: 720

    // The sddm user reads a world-readable, non-secret INI file. Missing or
    // invalid entries default to Omarchy without changing authentication.
    Settings {
        id: selection
        fileName: "/var/lib/omarchy-cyberpunk/selected-theme"
        category: "Theme"
        property string selected: "omarchy"
    }

    Loader {
        id: greeter
        anchors.fill: parent
        source: selection.selected === "cyberpunk"
            ? "file:///usr/share/sddm/themes/lightqv-cyberpunk/Main.qml"
            : "file:///usr/share/sddm/themes/omarchy/Main.qml"

        onLoaded: {
            if (item) {
                item.width = width
                item.height = height
            }
        }
        onStatusChanged: {
            if (status === Loader.Error && source.toString() !== "file:///usr/share/sddm/themes/omarchy/Main.qml") {
                console.warn("Cyberpunk greeter selector: failed to load " + source)
                source = "file:///usr/share/sddm/themes/omarchy/Main.qml"
            }
        }
    }
}
