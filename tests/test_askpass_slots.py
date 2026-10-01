"""Verify native askpass editing against custom visible insertion slots."""

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("askpass", ROOT / "askpass/askpass.py")
askpass = importlib.util.module_from_spec(spec)
spec.loader.exec_module(askpass)


class AskpassSlotsTest(unittest.TestCase):
    def test_shared_backdrop_is_opaque_and_dimmed_between_sequences(self):
        app = QApplication.instance() or QApplication([])
        image = QImage(64, 64, QImage.Format_RGB32)
        image.fill(QColor("white"))
        with patch.object(askpass.Askpass, "_capture_desktop", return_value=image):
            widget = askpass.Askpass("Offline backdrop test")
            widget.resize(640, 480)
            widget.show()
            widget.pulse.stop()
            widget.sync_fault_frame()
            QTest.qWait(50)
            frame = widget.fault_backdrop.grabFramebuffer()
            pixel = frame.pixelColor(320, 240)
            self.assertEqual(pixel.alpha(), 255)
            self.assertGreater(pixel.red(), 40)
            self.assertLess(pixel.red(), 130)
            widget.close()

    def test_fault_timer_continues_past_one_cycle_and_stops_when_hidden(self):
        app = QApplication.instance() or QApplication([])
        image = QImage(64, 64, QImage.Format_RGB32)
        image.fill(QColor("#123456"))
        with patch.object(askpass.Askpass, "_capture_desktop", return_value=image) as capture:
            widget = askpass.Askpass("Offline test")
            widget.resize(640, 480)
            widget.show()
            QTest.qWait(50)
            previous_duration = widget.fault_duration
            widget.started_at -= widget.fault_duration + widget.fault_pause + 1
            widget.advance_fault()
            self.assertNotEqual(widget.fault_duration, previous_duration)
            self.assertTrue(widget.pulse.isActive())
            self.assertEqual(capture.call_count, 1)
            widget.hide()
            self.assertFalse(widget.pulse.isActive())
            with patch.dict(os.environ, {"OMARCHY_REDUCED_MOTION": "1"}):
                widget.show()
                self.assertFalse(widget.pulse.isActive())
            widget.close()

    def test_sequence_speed_bags_shuffle_without_adjacent_repeats(self):
        app = QApplication.instance() or QApplication([])
        with patch.object(askpass.Askpass, "_capture_desktop", return_value=QImage()):
            widget = askpass.Askpass("Offline cadence test")
            durations = []
            for _ in range(30):
                widget.start_fault_sequence()
                durations.append(widget.fault_duration)
                self.assertGreaterEqual(widget.fault_pause, .35)
                self.assertLessEqual(widget.fault_pause, .80)
            for start in range(0, 30, 3):
                self.assertEqual(sorted(durations[start:start + 3]), sorted(widget.FAULT_SPEEDS))
            self.assertTrue(all(a != b for a, b in zip(durations, durations[1:])))
            widget.close()

    def test_edit_selection_scroll_and_empty_caret(self):
        app = QApplication.instance() or QApplication([])
        field = askpass.PasswordField(QColor("#ff435b"), QColor("#777777"))
        field.resize(381, 54)
        field.show()
        QTest.qWait(40)
        QTest.keyClicks(field, "abcdef")
        self.assertEqual(field.text(), "abcdef")
        QTest.mouseClick(field, Qt.LeftButton, pos=QPoint(96, 27))
        self.assertEqual(field.cursorPosition(), 2)
        QTest.keyClicks(field, "z")
        self.assertEqual(field.text(), "abzcdef")
        QTest.mouseClick(field, Qt.LeftButton, Qt.ShiftModifier, QPoint(136, 27))
        self.assertEqual(field.selectedText(), "c")
        QTest.keyClicks(field, "x")
        self.assertEqual(field.text(), "abzxdef")
        QTest.keyClick(field, Qt.Key_End)
        QTest.keyClicks(field, "a" * 50)
        self.assertGreater(field.first_slot, 0)
        QTest.keyClick(field, Qt.Key_Home)
        self.assertEqual(field.first_slot, 0)
        QTest.keyClick(field, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClick(field, Qt.Key_Backspace)
        self.assertEqual(field.text(), "")
        app.processEvents()
        image = field.grab().toImage()
        caret = image.pixelColor(60, 20)
        self.assertEqual(caret, field.red)
        # Three thin edges; a four-pixel left accent, with no native white caret.
        self.assertEqual(image.pixelColor(2, 27), field.red)
        self.assertEqual(image.pixelColor(380, 27), field.red)
        self.assertNotEqual(image.pixelColor(379, 27), field.red)
        field.close()


if __name__ == "__main__":
    unittest.main()
