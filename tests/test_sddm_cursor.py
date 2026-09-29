"""Exercise the visible mask cursor against the real offline greeter input."""

import importlib.util
import os
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from PySide6.QtCore import QPoint, QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

loader = SourceFileLoader("offline_greeter", str(ROOT / "scripts/preview-sddm"))
spec = importlib.util.spec_from_loader(loader.name, loader)
offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offline)


class GreeterCursorTest(unittest.TestCase):
    def test_cursor_follows_keyboard_and_glyph_clicks(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        view = QQuickView()
        view.rootContext().setContextProperty("sessionModel", offline.Sessions(view))
        view.rootContext().setContextProperty("userModel", offline.Users(view))
        view.rootContext().setContextProperty("sddm", offline.Auth(view))
        view.setResizeMode(QQuickView.SizeRootObjectToView)
        view.resize(1920, 1080)
        view.setSource(QUrl.fromLocalFile(str(ROOT / "sddm-theme/Main.qml")))
        self.assertEqual(view.status(), QQuickView.Ready)
        view.show()
        app.processEvents()
        field = view.rootObject().findChild(QObject, "passwordInput")
        self.assertIsNotNone(field)
        field.setProperty("text", "abcdef")
        field.forceActiveFocus()
        field.setProperty("cursorPosition", 6)
        QTest.keyClick(view, Qt.Key_Left)
        app.processEvents()
        self.assertEqual(field.property("cursorPosition"), 5)
        QTest.keyClick(view, Qt.Key_Backspace)
        app.processEvents()
        self.assertEqual(field.property("text"), "abcdf")
        self.assertEqual(field.property("cursorPosition"), 4)
        # The visible masks start at x=859 at this resolution, at 15px steps.
        mask = view.rootObject().findChild(QObject, "maskMouseArea")
        self.assertIsNotNone(mask)
        position = mask.mapToScene(QPoint(44, 14))
        QTest.mouseClick(view, Qt.LeftButton, pos=position.toPoint())
        app.processEvents()
        self.assertEqual(field.property("cursorPosition"), 2)
        QTest.keyClick(view, Qt.Key_Z, Qt.NoModifier, 0)
        app.processEvents()
        self.assertEqual(field.property("text"), "abzcdf")
        self.assertEqual(field.property("cursorPosition"), 3)
        view.close()


if __name__ == "__main__":
    unittest.main()
