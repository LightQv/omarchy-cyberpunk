import QtQuick
import QtQuick.Shapes

// Presentation only: the native input retains editing and authentication.
Item {
  id: root
  required property var input
  property color accent: "#ff435b"
  property color selectionColor: "#5553e3d2"
  property bool caretEnabled: true
  property real rightReserve: 0
  readonly property int slotWidth: 20
  readonly property int cursorGap: 8
  readonly property int capacity: Math.max(1, Math.floor((glyphs.width - 4 - cursorGap) / slotWidth))
  property int firstSlot: 0

  function ensureCursorVisible() {
    if (!input) return
    var cursor = input.cursorPosition
    if (cursor < firstSlot) firstSlot = cursor
    else if (cursor > firstSlot + capacity) firstSlot = cursor - capacity
    firstSlot = Math.max(0, Math.min(firstSlot, Math.max(0, input.text.length - capacity)))
  }
  onCapacityChanged: ensureCursorVisible()
  Connections {
    target: root.input
    function onTextChanged() { root.ensureCursorVisible() }
    function onCursorPositionChanged() { root.ensureCursorVisible() }
  }
  Item {
    id: glyphs
    x: 56; width: parent.width - 80 - root.rightReserve
    height: parent.height * 0.54
    anchors.verticalCenter: parent.verticalCenter
    clip: true
    Repeater {
      model: Math.min(root.capacity, Math.max(0, root.input.text.length - root.firstSlot))
      Item {
        x: index * root.slotWidth + 4 + (position >= root.input.cursorPosition ? root.cursorGap : 0)
        width: 14; height: glyphs.height
        readonly property int position: root.firstSlot + index
        Rectangle {
          x: -3; width: root.slotWidth; height: parent.height
          visible: parent.position >= root.input.selectionStart && parent.position < root.input.selectionEnd
          color: root.selectionColor
        }
        Shape {
          anchors.fill: parent
          ShapePath {
            strokeWidth: 1.4; strokeColor: root.accent
            fillColor: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 50 / 255)
            startX: 1; startY: 1
            PathLine { x: 13; y: 1 }
            PathLine { x: 13; y: glyphs.height - 5 }
            PathLine { x: 9; y: glyphs.height - 1 }
            PathLine { x: 1; y: glyphs.height - 1 }
            PathLine { x: 1; y: 1 }
          }
        }
      }
    }
    Rectangle {
      x: (root.input.cursorPosition - root.firstSlot) * root.slotWidth + root.cursorGap / 2
      y: 2; width: 2; height: parent.height - 4
      color: root.accent
      visible: root.input.activeFocus && root.caretEnabled
    }
  }
  MouseArea {
    anchors.fill: parent
    anchors.rightMargin: root.rightReserve
    enabled: root.input.enabled && !root.input.readOnly
    property int anchorPosition: 0
    function positionAt(x) {
      var local = x - 56
      var gapStart = (root.input.cursorPosition - root.firstSlot) * root.slotWidth
      if (local > gapStart && local < gapStart + root.cursorGap) return root.input.cursorPosition
      if (local >= gapStart + root.cursorGap) local -= root.cursorGap
      return Math.max(0, Math.min(root.input.text.length, root.firstSlot + Math.round(local / root.slotWidth)))
    }
    onPressed: function(mouse) {
      root.input.forceActiveFocus()
      if (mouse.modifiers & Qt.ShiftModifier) {
        anchorPosition = root.input.selectionStart === root.input.cursorPosition ? root.input.selectionEnd : root.input.selectionStart
        root.input.select(anchorPosition, positionAt(mouse.x))
      } else {
        anchorPosition = positionAt(mouse.x)
        root.input.cursorPosition = anchorPosition
      }
    }
    onPositionChanged: function(mouse) {
      if (pressed) root.input.select(anchorPosition, positionAt(mouse.x))
    }
  }
}
