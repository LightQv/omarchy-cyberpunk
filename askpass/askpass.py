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

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QCursor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtQuickWidgets import QQuickWidget


class FrozenImageProvider(QQuickImageProvider):
    """Supply the captured still directly to QML without writing screen pixels."""

    def __init__(self, image):
        super().__init__(QQuickImageProvider.Image)
        self.image = image.copy()

    def requestImage(self, _id, size, requested_size):
        size.setWidth(self.image.width())
        size.setHeight(self.image.height())
        return self.image


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
        state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'omarchy-cyberpunk/scheme.json'
        if state.is_file():
            import json
            if json.loads(state.read_text()).get('scheme') == 'inverted':
                defaults['red'], defaults['cyan'] = defaults['cyan'], defaults['red']
                defaults['bright_red'] = defaults['red']
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        pass
    return defaults


class PasswordField(QLineEdit):
    """Keep native password editing; draw beveled length-only masks over it."""

    CURSOR_GAP = 8

    def __init__(self, red: QColor, muted: QColor) -> None:
        super().__init__()
        self.red, self.muted = red, muted
        self.first_slot = 0
        self.drag_anchor = 0
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setFixedHeight(54)
        self.setTextMargins(56, 0, 20, 0)
        self.textChanged.connect(self.sync_slots)
        self.cursorPositionChanged.connect(self.sync_slots)
        self.selectionChanged.connect(self.update)

    @staticmethod
    def logical_length(text: str) -> int:
        # Qt's cursor/selection positions use QString (UTF-16) offsets.
        return len(text.encode("utf-16-le", errors="surrogatepass")) // 2

    def sync_slots(self, *_args) -> None:
        capacity = max(1, int((self.width() - 84 - self.CURSOR_GAP) // 20))
        cursor = self.cursorPosition()
        if cursor < self.first_slot:
            self.first_slot = cursor
        elif cursor > self.first_slot + capacity:
            self.first_slot = cursor - capacity
        self.first_slot = max(0, min(self.first_slot, max(0, self.logical_length(self.text()) - capacity)))
        self.update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.sync_slots()

    def position_at(self, x: float) -> int:
        local = x - 56
        gap_start = (self.cursorPosition() - self.first_slot) * 20
        if gap_start < local < gap_start + self.CURSOR_GAP:
            return self.cursorPosition()
        if local >= gap_start + self.CURSOR_GAP:
            local -= self.CURSOR_GAP
        return max(0, min(self.logical_length(self.text()),
                          self.first_slot + math.floor(local / 20 + 0.5)))

    def mousePressEvent(self, event) -> None:
        """Place the native edit cursor at the clicked custom mask gap."""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            start = self.selectionStart()
            end = start + self.logical_length(self.selectedText())
            self.drag_anchor = end if start == self.cursorPosition() else self.cursorPosition() if start < 0 else start
            position = self.position_at(event.position().x())
            self.setSelection(self.drag_anchor, position - self.drag_anchor)
        else:
            self.drag_anchor = self.position_at(event.position().x())
            self.setCursorPosition(self.drag_anchor)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            position = self.position_at(event.position().x())
            self.setSelection(self.drag_anchor, position - self.drag_anchor)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selectAll()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def paintEvent(self, event) -> None:
        # Paint the field ourselves: native QLineEdit cursor/selection geometry
        # must not bleed through the custom logical-slot renderer.
        painter = QPainter(self)
        background = QColor(self.red)
        background.setAlpha(22)
        painter.fillRect(self.rect(), background)
        painter.fillRect(QRectF(0, 0, 4, self.height()), self.red)
        painter.fillRect(QRectF(0, 0, self.width(), 1), self.red)
        painter.fillRect(QRectF(0, self.height() - 1, self.width(), 1), self.red)
        painter.fillRect(QRectF(self.width() - 1, 0, 1, self.height()), self.red)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("JetBrainsMono Nerd Font", 13))
        painter.setPen(self.red)
        painter.drawText(QRectF(24, 0, 19, self.height()), Qt.AlignmentFlag.AlignVCenter, ">")
        count = self.logical_length(self.text())
        if not count:
            painter.setPen(self.muted)
            painter.drawText(QRectF(56, 0, self.width() - 112, self.height()),
                              Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, "ENTER PASSWORD")
        top, height = self.height() * 0.23, self.height() * 0.54
        capacity = max(1, int((self.width() - 84 - self.CURSOR_GAP) // 20))
        selection_start = self.selectionStart()
        selection_end = selection_start + self.logical_length(self.selectedText())
        painter.setClipRect(QRectF(56, top, self.width() - 80, height))
        fill = QColor(self.red)
        fill.setAlpha(50)
        for index in range(min(capacity, count - self.first_slot)):
            position = self.first_slot + index
            left = 60 + index * 20 + (self.CURSOR_GAP if position >= self.cursorPosition() else 0)
            if selection_start <= position < selection_end:
                painter.fillRect(QRectF(left - 3, top, 20, height), QColor("#5553e3d2"))
            painter.setBrush(fill)
            painter.setPen(QPen(self.red, 1.4))
            shape = QPainterPath(QPointF(left + 1, top + 1))
            shape.lineTo(left + 13, top + 1)
            shape.lineTo(left + 13, top + height - 5)
            shape.lineTo(left + 9, top + height - 1)
            shape.lineTo(left + 1, top + height - 1)
            shape.closeSubpath()
            painter.drawPath(shape)
        if self.hasFocus() and self.isEnabled() and not self.isReadOnly():
            painter.fillRect(QRectF(56 + self.CURSOR_GAP / 2 + (self.cursorPosition() - self.first_slot) * 20,
                                   top + 2, 2, height - 4), self.red)


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
    FAULT_SPEEDS = (.85, 1.1, 1.4)

    def __init__(self, prompt: str) -> None:
        super().__init__()
        colors = theme_colors()
        self.red = QColor(colors["red"])
        self.cyan = QColor(colors["cyan"])
        self.base = QColor(colors["darker_background"])
        self.scene = self._capture_desktop()
        self.fault_backdrop = None
        self.background_size = None
        self.variant = random.SystemRandom().randrange(4)
        self.started_at = 0.0
        self.fault_duration = self.FAULT_DURATION
        self.fault_pause = 0.25
        self.speed_bag = []
        self.last_speed = None
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
        if not self.scene.isNull():
            self.install_fault_backdrop(self.scene)

    def install_fault_backdrop(self, image):
        """Render exactly the same frozen-fragment effect as Polkit."""
        self.fault_backdrop = QQuickWidget(self)
        self.fault_backdrop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fault_backdrop.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.fault_backdrop.setClearColor(Qt.GlobalColor.transparent)
        self.fault_backdrop.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.frozen_provider = FrozenImageProvider(image)
        self.fault_backdrop.engine().addImageProvider("askpass", self.frozen_provider)
        self.fault_backdrop.setSource(QUrl.fromLocalFile(str(Path(__file__).with_name("FaultBackdrop.qml"))))
        if self.fault_backdrop.rootObject():
            self.fault_backdrop.rootObject().setProperty("red", self.red)
            self.fault_backdrop.rootObject().setProperty("cyan", self.cyan)
            self.fault_backdrop.rootObject().setProperty("background", self.base)
        self.fault_backdrop.setGeometry(self.rect())
        self.fault_backdrop.lower()
        self.fault_backdrop.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fault_backdrop:
            self.fault_backdrop.setGeometry(self.rect())

    def sync_fault_frame(self):
        if self.fault_backdrop and self.fault_backdrop.rootObject():
            phase = min(1.0, (time.monotonic() - self.started_at) / self.fault_duration) if self.pulse.isActive() else 1.0
            self.fault_backdrop.rootObject().setProperty("phase", phase)
            self.fault_backdrop.rootObject().setProperty("variant", self.variant)

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
        """Repeat cosmetic beats over the same frozen image until hidden."""
        if not self.isVisible():
            self.pulse.stop()
        elif time.monotonic() - self.started_at >= self.fault_duration + self.fault_pause:
            self.start_fault_sequence()
        self.sync_fault_frame()
        self.update()

    def start_fault_sequence(self) -> None:
        if not self.speed_bag:
            self.speed_bag = list(self.FAULT_SPEEDS)
        choices = [speed for speed in self.speed_bag if speed != self.last_speed]
        self.fault_duration = random.SystemRandom().choice(choices)
        self.speed_bag.remove(self.fault_duration)
        self.last_speed = self.fault_duration
        self.fault_pause = random.SystemRandom().uniform(0.35, 0.80)
        self.variant = (self.variant + random.SystemRandom().randrange(1, 4)) % 4
        self.started_at = time.monotonic()

    def paintEvent(self, event) -> None:
        """Render frozen desktop faults underneath the still-live Qt controls."""
        super().paintEvent(event)
        painter = QPainter(self)
        if not self.scene.isNull():
            if self.background_size != self.size():
                self.background_size = self.size()
                sharp = self.frozen_provider.image if self.fault_backdrop else self.scene
                original = sharp.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
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
        self.start_fault_sequence()
        if not self.scene.isNull() and os.environ.get("OMARCHY_REDUCED_MOTION") != "1":
            self.pulse.start()
        QTimer.singleShot(0, self, self.password.setFocus)

    def hideEvent(self, event) -> None:
        self.pulse.stop()
        super().hideEvent(event)

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
        self.pulse.stop()
        QApplication.instance().exit(0)

    def reject(self) -> None:
        self.pulse.stop()
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
