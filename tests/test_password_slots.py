"""Exercise the retained native input and shared lock/Polkit presentation."""

import os
from pathlib import Path
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtCore import QPoint, QObject, QMetaObject, Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]


def type_keys(view, text):
    for character in text:
        QTest.keyClick(view, Qt.Key(ord(character.upper())))


class PasswordSlotsTest(unittest.TestCase):
    def test_shared_input_edit_selection_and_long_password_scroll(self):
        app = QApplication.instance() or QApplication([])
        view = QQuickView()
        view.setSource(QUrl.fromLocalFile(str(ROOT / "tests/fixtures/password-slots.qml")))
        self.assertEqual(view.status(), QQuickView.Ready)
        view.show()
        QTest.qWait(40)
        field = view.rootObject().findChild(QObject, "testInput")
        slots = view.rootObject().findChild(QObject, "testSlots")
        self.assertTrue(field.hasActiveFocus())
        type_keys(view, "abcdef")
        QTest.mouseClick(view, Qt.LeftButton, pos=QPoint(96, 27))
        self.assertEqual(field.property("cursorPosition"), 2)
        QTest.mouseClick(view, Qt.LeftButton, Qt.ShiftModifier, QPoint(144, 27))
        self.assertEqual(field.property("selectedText"), "cd")
        type_keys(view, "x")
        self.assertEqual(field.property("text"), "abxef")
        QTest.keyClick(view, Qt.Key_End)
        type_keys(view, "a" * 50)
        self.assertGreater(slots.property("firstSlot"), 0)
        QTest.keyClick(view, Qt.Key_Home)
        self.assertEqual(slots.property("firstSlot"), 0)
        self.assertEqual(slots.property("slotWidth"), 20)
        self.assertEqual(slots.property("cursorGap"), 8)
        view.close()

    def test_loop_and_reduced_motion_do_not_change_one_shot_lock_contract(self):
        app = QApplication.instance() or QApplication([])
        view = QQuickView()
        view.setSource(QUrl.fromLocalFile(str(ROOT / "tests/fixtures/rhythm.qml")))
        self.assertEqual(view.status(), QQuickView.Ready)
        view.show()
        rhythm = view.rootObject().findChild(QObject, "testRhythm")
        QTest.qWait(2500)
        self.assertGreaterEqual(rhythm.property("sequencesStarted"), 2)
        rhythm.setProperty("repeatWhileVisible", False)
        self.assertEqual(rhythm.property("phase"), 1)
        rhythm.setProperty("reducedMotion", True)
        rhythm.setProperty("repeatWhileVisible", True)
        QTest.qWait(50)
        self.assertEqual(rhythm.property("phase"), 1)
        rhythm.setProperty("repeatWhileVisible", False)
        rhythm.setProperty("reducedMotion", False)
        self.assertTrue(QMetaObject.invokeMethod(rhythm, "play"))
        QTest.qWait(150)
        self.assertLess(rhythm.property("phase"), 1)
        QTest.qWait(800)
        self.assertEqual(rhythm.property("phase"), 1)
        view.close()
