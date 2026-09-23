#!/usr/bin/python
"""Graphical sudo askpass: only the accepted password is written to stdout."""

import os
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


RED = "#ff3045"
CYAN = "#53e3d2"
TEXT = "#e5f1ee"
BASE = "#0c1015"


class Askpass(QWidget):
    """Show a fullscreen modal; transmit the password only through stdout."""

    def __init__(self, prompt: str) -> None:
        super().__init__()
        self.setWindowTitle("Authentication required")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("overlay")
        self.setStyleSheet(
            f"""
            QWidget#overlay {{ background: #080c12; color: {TEXT}; }}
            QFrame#frame {{ background: {BASE}; border: 1px solid {CYAN}; }}
            QLabel {{ background: transparent; border: 0; color: {TEXT}; }}
            QLabel#eyebrow {{ color: {RED}; font-size: 12px; font-weight: bold; }}
            QLabel#title {{ color: {TEXT}; font-size: 25px; font-weight: bold; }}
            QLabel#description {{ color: #b7d1cb; font-size: 12px; }}
            QLabel#footer {{ color: {CYAN}; font-size: 11px; }}
            QLineEdit {{ background: #101d21; color: {TEXT}; border: 1px solid {CYAN};
                         border-left: 4px solid {RED}; padding: 13px; font-size: 16px; }}
            QLineEdit:focus {{ border: 1px solid {CYAN}; border-left: 4px solid {RED}; }}
            QPushButton {{ background: #101d21; color: {CYAN}; border: 1px solid {CYAN};
                           padding: 10px 16px; font-size: 12px; font-weight: bold; }}
            QPushButton#authorize {{ background: {RED}; color: #080c12; border: 1px solid {RED}; }}
            QPushButton:hover {{ background: #214145; }}
            QPushButton#authorize:hover {{ background: #ff6474; }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        frame = QFrame(self)
        frame.setObjectName("frame")
        frame.setFixedWidth(590)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(32, 30, 32, 26)
        layout.setSpacing(16)

        eyebrow = QLabel("//  NEURAL ACCESS  /  AUTHORIZATION")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("IDENTITY VERIFICATION")
        title.setObjectName("title")
        layout.addWidget(title)

        description = QLabel(prompt.strip() or "Authentication is required")
        description.setObjectName("description")
        description.setTextFormat(Qt.TextFormat.PlainText)
        description.setWordWrap(True)
        layout.addWidget(description)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("ENTER PASSPHRASE")
        self.password.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.password.returnPressed.connect(self.accept)
        layout.addWidget(self.password)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("ABORT")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        authorize = QPushButton("AUTHORIZE")
        authorize.setObjectName("authorize")
        authorize.clicked.connect(self.accept)
        actions.addWidget(authorize)
        layout.addLayout(actions)

        footer = QLabel("ESC  ABORT   //   ENTER  CONFIRM")
        footer.setObjectName("footer")
        layout.addWidget(footer)
        outer.addWidget(frame)

        self.setFont(QFont("JetBrainsMono Nerd Font", 11))

    def paintEvent(self, event) -> None:
        """Draw a quiet screen-space grid outside the authentication frame."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(83, 227, 210, 18), 1))
        for x in range(0, self.width(), 64):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 64):
            painter.drawLine(0, y, self.width(), y)
        painter.setPen(QPen(QColor(255, 48, 69, 100), 2))
        painter.drawLine(0, round(self.height() * 0.15), self.width(), round(self.height() * 0.15))
        painter.drawLine(0, round(self.height() * 0.85), self.width(), round(self.height() * 0.85))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.password.setFocus)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def accept(self) -> None:
        secret = self.password.text()
        self.password.clear()
        if not secret:
            self.password.setFocus()
            return
        os.write(sys.stdout.fileno(), secret.encode("utf-8") + b"\n")
        QApplication.instance().exit(0)

    def reject(self) -> None:
        self.password.clear()
        QApplication.instance().exit(1)


def main() -> int:
    # sudo supplies its prompt as an argument. Never let Qt parse it as a flag.
    app = QApplication([sys.argv[0]])
    window = Askpass(" ".join(sys.argv[1:]))
    screen = app.screenAt(QCursor.pos()) or app.primaryScreen()
    if screen:
        window.setGeometry(screen.geometry())
        for frame in window.findChildren(QFrame):
            if frame.objectName() == "frame":
                frame.setFixedWidth(min(590, max(200, screen.geometry().width() - 32)))
    window.showFullScreen()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
