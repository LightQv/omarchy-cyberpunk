#!/usr/bin/python
"""Theme-scoped sudo askpass; only an accepted password goes to stdout."""

import os
import math
import random
import subprocess
import sys
import time
import tomllib
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)


def theme_colors() -> dict[str, str]:
    """Read the active Cyberpunk palette, retaining defaults when unavailable."""
    defaults = {
        "red": "#ff3045", "cyan": "#53e3d2", "foreground": "#e5f1ee",
        "background": "#0c1015", "light_foreground": "#b7bbbd",
        "bright_red": "#ff6474", "darker_background": "#07090e",
    }
    try:
        path = Path.home() / ".config/omarchy/themes/cyberpunk/colors.toml"
        palette = tomllib.loads(path.read_text())
        for key in defaults:
            if isinstance(palette.get(key), str) and QColor(palette[key]).isValid():
                defaults[key] = palette[key]
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        pass
    return defaults


class PasswordField(QLineEdit):
    """Keep native password editing; draw beveled length-only masks over it."""

    def __init__(self, red: QColor, muted: QColor) -> None:
        super().__init__()
        self.red, self.muted = red, muted
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setFixedHeight(54)
        self.setTextMargins(56, 0, 20, 0)
        self.textChanged.connect(self.update)
        self.cursorPositionChanged.connect(self.update)

    def mousePressEvent(self, event) -> None:
        """Place the native edit cursor at the clicked custom mask gap."""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self.text():
            step = min(20.0, (self.width() - 80) / len(self.text()))
            position = round((event.position().x() - 58) / step)
            self.setCursorPosition(max(0, min(len(self.text()), position)))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("JetBrainsMono Nerd Font", 13))
        painter.setPen(self.red)
        painter.drawText(QRectF(24, 0, 19, self.height()), Qt.AlignmentFlag.AlignVCenter, ">")
        count = len(self.text())
        if not count:
            painter.setPen(self.muted)
            painter.drawText(QRectF(56, 0, self.width() - 76, self.height()),
                             Qt.AlignmentFlag.AlignVCenter, "ENTER PASSWORD")
            return

        step = min(20.0, (self.width() - 80) / count)
        glyph = min(14.0, step * 0.76)
        top, height = self.height() * 0.23, self.height() * 0.54
        fill = QColor(self.red)
        fill.setAlpha(50)
        painter.setBrush(fill)
        painter.setPen(QPen(self.red, 1.4))
        for index in range(count):
            left = 56 + index * step
            shape = QPainterPath(QPointF(left + 1, top))
            shape.lineTo(left + glyph, top)
            shape.lineTo(left + glyph, top + height - 5)
            shape.lineTo(left + glyph - min(5, glyph * 0.35), top + height)
            shape.lineTo(left + 1, top + height)
            shape.closeSubpath()
            painter.drawPath(shape)
        painter.fillRect(QRectF(min(self.width() - 22, 58 + self.cursorPosition() * step), top + 2,
                                2, height - 4), self.red)


class BeveledButton(QPushButton):
    """A quiet cut-corner submit action shared visually with the lock."""

    def __init__(self, text: str, red: QColor) -> None:
        super().__init__(text)
        self.red = red
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        shape = QPainterPath(QPointF(22, 0.5))
        shape.lineTo(self.width() - 0.5, 0.5)
        shape.lineTo(self.width() - 0.5, self.height() - 9)
        shape.lineTo(self.width() - 9, self.height() - 0.5)
        shape.lineTo(0.5, self.height() - 0.5)
        shape.lineTo(0.5, 22)
        shape.closeSubpath()
        fill = QColor(self.red)
        fill.setAlpha(64 if self.isDown() else 22)
        painter.fillPath(shape, fill)
        border = QColor(self.red)
        border.setAlpha(230 if self.underMouse() or self.hasFocus() else 170)
        painter.setPen(QPen(border, 1))
        painter.drawPath(shape)
        font = QFont("JetBrainsMono Nerd Font", 12)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        painter.setPen(self.red)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class Askpass(QWidget):
    """Show a lock-inspired modal without changing sudo's password transport."""

    # A four-beat F/S/S/F motif. Band placement is rotated per invocation.
    FAULT_DURATION = 0.76
    BEAT_STARTS = (0.0, 0.19, 0.50, 0.83)
    BEAT_LENGTHS = (0.13, 0.24, 0.26, 0.13)
    BANDS = (
        (0.04, 0.17, 0.32, 8, 19, 0), (0.55, 0.24, 0.40, 9, -27, 1),
        (0.16, 0.38, 0.55, 7, 31, 2), (0.51, 0.49, 0.40, 11, -22, 1),
        (0.05, 0.67, 0.36, 6, 25, 3), (0.35, 0.76, 0.57, 10, -24, 2),
        (0.03, 0.87, 0.30, 7, 17, 3), (0.73, 0.82, 0.23, 5, -14, 0),
        (0.11, 0.27, 34, 34, -22, 0), (0.30, 0.13, 42, 42, 29, 2),
        (0.06, 0.46, 30, 30, 18, 1), (0.88, 0.69, 28, 28, -26, 3),
        (0.19, 0.79, 40, 40, 27, 2), (0.69, 0.91, 26, 26, -20, 3),
    )

    def __init__(self, prompt: str) -> None:
        super().__init__()
        colors = theme_colors()
        self.red = QColor(colors["red"])
        self.cyan = QColor(colors["cyan"])
        self.base = QColor(colors["darker_background"])
        self.scene = self._capture_desktop()
        self.negative = QImage()
        self.variant = random.SystemRandom().randrange(4)
        self.started_at = 0.0
        self.setWindowTitle("Authorization required")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("overlay")
        self.setStyleSheet(f"""
            QWidget#overlay {{ background: transparent; color: {colors['foreground']}; }}
            QFrame#frame {{ background: transparent; border: none; }}
            QLabel {{ background: transparent; border: none; color: {colors['foreground']}; }}
            QLabel#eyebrow {{ color: {colors['red']}; font-size: 13px; font-weight: bold; }}
            QLabel#muted {{ color: {colors['light_foreground']}; font-size: 12px; }}
            QLabel#user {{ color: {colors['foreground']}; font-size: 12px; }}
            QLabel#description {{ color: {colors['light_foreground']}; font-size: 11px; }}
            QLabel#footer {{ color: {colors['light_foreground']}; font-size: 11px; }}
            QLineEdit {{ background: rgba({self.red.red()}, {self.red.green()}, {self.red.blue()}, 22); color: transparent; border: 1px solid {colors['red']}; border-left-width: 4px; }}
            QPushButton#abort {{ background: transparent; color: {colors['light_foreground']}; border: none; font-size: 11px; text-align: left; padding: 0; }}
        """)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame = QFrame(self)
        frame.setObjectName("frame")
        frame.setFixedWidth(451)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(25, 0, 35, 0)
        layout.setSpacing(12)

        eyebrow = QLabel("// AUTHENTICATION SEQUENCE")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        controls = QVBoxLayout()
        controls.setContentsMargins(10, 0, 0, 0)
        controls.setSpacing(12)
        layout.addLayout(controls)
        identity = QHBoxLayout()
        user_label = QLabel("USER")
        user_label.setObjectName("muted")
        identity.addWidget(user_label)
        identity.addStretch()
        user = QLabel((os.environ.get("USER") or "LOCAL USER").upper())
        user.setObjectName("user")
        identity.addWidget(user)
        controls.addLayout(identity)

        description = QLabel(prompt.strip() or "Authorization is required")
        description.setObjectName("description")
        description.setTextFormat(Qt.TextFormat.PlainText)
        description.setWordWrap(True)
        controls.addWidget(description)

        self.password = PasswordField(self.red, QColor(colors["light_foreground"]))
        self.password.returnPressed.connect(self.accept)
        controls.addWidget(self.password)
        submit = BeveledButton("SUBMIT", self.red)
        submit.clicked.connect(self.accept)
        controls.addWidget(submit)
        cancel = QPushButton("ESC  ABORT   /   ENTER  CONFIRM")
        cancel.setObjectName("abort")
        cancel.clicked.connect(self.reject)
        controls.addWidget(cancel)
        outer.addWidget(frame)
        self.setFont(QFont("JetBrainsMono Nerd Font", 11))

        self.pulse = QTimer(self)
        self.pulse.setInterval(16)
        self.pulse.timeout.connect(self.advance_fault)

    @staticmethod
    def _capture_desktop() -> QImage:
        """Capture before showing the modal, in memory; never write screen pixels."""
        if not os.environ.get("WAYLAND_DISPLAY") or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return QImage()
        try:
            result = subprocess.run(["grim", "-t", "png", "-"], capture_output=True,
                                    timeout=0.7, check=True)
            return QImage.fromData(result.stdout, "PNG")
        except (OSError, subprocess.SubprocessError):
            return QImage()

    def advance_fault(self) -> None:
        """Stop the cosmetic pulse after one four-beat cycle."""
        if time.monotonic() - self.started_at >= self.FAULT_DURATION:
            self.pulse.stop()
        self.update()

    def paintEvent(self, event) -> None:
        """Render frozen desktop faults underneath the still-live Qt controls."""
        super().paintEvent(event)
        painter = QPainter(self)
        if not self.scene.isNull():
            if self.scene.size() != self.size() or self.negative.isNull():
                original = self.scene.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
                self.negative = original.copy()
                self.negative.invertPixels()
                softened = original.scaled(max(1, self.width() // 12),
                                            max(1, self.height() // 12),
                                            Qt.AspectRatioMode.IgnoreAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                self.scene = softened.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            painter.drawImage(self.rect(), self.scene)
        scrim = QColor(self.base)
        scrim.setAlpha(170)
        painter.fillRect(self.rect(), scrim)

        elapsed = time.monotonic() - self.started_at
        if not self.pulse.isActive() or self.scene.isNull():
            self._paint_header(painter)
            return
        phase = elapsed / self.FAULT_DURATION
        for index, (x, y, width, height, shift, base_beat) in enumerate(self.BANDS):
            beat = (base_beat + self.variant) % 4
            local = (phase - self.BEAT_STARTS[beat]) / self.BEAT_LENGTHS[beat]
            if not 0 < local < 1:
                continue
            level = min(1.0, local / 0.18, (1 - local) / 0.28)
            target = QRectF(self.width() * x, self.height() * y,
                            width if width >= 1 else self.width() * width, height)
            source = QRectF(target.translated(shift * level, 0))
            sample_x = max(0, min(self.scene.width() - 1, round(source.center().x())))
            sample_y = max(0, min(self.scene.height() - 1, round(source.center().y())))
            sample = self.scene.pixelColor(sample_x, sample_y)
            chroma = max(sample.red(), sample.green(), sample.blue()) - min(
                sample.red(), sample.green(), sample.blue())
            inverted = (index + self.variant) % 2 and chroma >= 38
            image = self.negative if inverted else self.scene
            painter.save()
            # Keep the negative fully coloured rather than blending it back
            # toward grey with the backdrop at half opacity.
            painter.setOpacity(min(1.0, level * 4) if image is self.negative else level * 0.82)
            painter.drawImage(target, image, source)
            painter.restore()
            if not inverted:
                painter.save()
                painter.setOpacity(level * 0.22)
                painter.fillRect(target, self.red)
                painter.restore()
            accent = QColor(self.cyan if index % 3 == 1 else self.red)
            accent.setAlpha(round(level * 130))
            painter.setPen(QPen(accent, 1))
            painter.drawLine(QPointF(target.left(), target.top()),
                             QPointF(target.left() + target.width() * 0.56, target.top()))
        self._paint_header(painter)

    def _paint_header(self, painter: QPainter) -> None:
        """Keep the curved corner labels outside the password composition."""
        painter.setPen(QPen(self.red, 1))
        font = QFont("JetBrainsMono Nerd Font")
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        self._paint_curved_label(painter, "//  LOCAL  /  PRIVILEGED ACCESS",
                                 self.width() * 0.023, self.height() * 0.045)
        right = "AUTHORIZATION REQUIRED"
        self._paint_curved_label(painter, right,
                                 self.width() * 0.97 - painter.fontMetrics().horizontalAdvance(right),
                                 self.height() * 0.045, right_side=True)

    @staticmethod
    def _paint_curved_label(painter: QPainter, text: str, x: float, y: float,
                            right_side: bool = False) -> None:
        """Bow each label's inner end down, using the same shallow arc as QML."""
        metrics = painter.fontMetrics()
        total = max(1, metrics.horizontalAdvance(text))
        advance = 0
        depth = 8
        slope = (-1 if right_side else 1) * depth / total
        for glyph in text:
            step = metrics.horizontalAdvance(glyph)
            inward = (advance + step / 2) / total
            if right_side:
                inward = 1 - inward
            painter.save()
            painter.translate(x + advance, y + depth * inward)
            painter.rotate(math.degrees(math.atan(slope)))
            painter.drawText(QPointF(0, 0), glyph)
            painter.restore()
            advance += step

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.started_at = time.monotonic()
        if not self.scene.isNull():
            self.pulse.start()
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
    app = QApplication([sys.argv[0]])
    window = Askpass(" ".join(sys.argv[1:]))
    screen = app.screenAt(QCursor.pos()) or app.primaryScreen()
    if screen:
        window.setGeometry(screen.geometry())
    window.showFullScreen()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
