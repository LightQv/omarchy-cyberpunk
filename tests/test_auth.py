"""Exercise askpass transport and precise Bash stanza ownership without sudo."""

import os
from pathlib import Path
import pty
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "askpass"))
from askpass import Askpass  # noqa: E402


class AuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_askpass_writes_only_accepted_secret(self):
        widget = Askpass("[sudo] password for test-user:")
        self.assertTrue(any("test-user" in label.text() for label in widget.findChildren(QLabel)))
        with patch("askpass.os.write") as write:
            widget.password.setText("not-a-real-password")
            widget.reject()
            write.assert_not_called()
            widget.password.setText("not-a-real-password")
            widget.accept()
            write.assert_called_once_with(1, b"not-a-real-password\n")
        self.assertEqual(widget.password.text(), "")
        widget.close()

    def test_askpass_mask_cursor_tracks_editing_and_clicks(self):
        widget = Askpass("Authorization required")
        widget.show()
        field = widget.password
        field.setText("abcd")
        field.setFocus()
        field.setCursorPosition(4)
        QTest.keyClick(field, Qt.Key_Left)
        self.assertEqual(field.cursorPosition(), 3)
        QTest.mouseClick(field, Qt.LeftButton, pos=QPoint(98, 27))
        self.assertEqual(field.cursorPosition(), 2)
        QTest.keyClick(field, Qt.Key_Backspace)
        self.assertEqual(field.text(), "acd")
        self.assertEqual(field.cursorPosition(), 1)
        self.assertIn("background: rgba(255, 48, 69, 22)", widget.styleSheet())
        field.clearFocus()
        widget.hide()
        self.app.processEvents()
        widget.close()
        widget.deleteLater()
        self.app.processEvents()

    def test_bashrc_stanza_round_trip_and_refuses_edited_marker(self):
        original = "# Personal shell settings\nexport TEST_FLAG=1\n"
        with tempfile.TemporaryDirectory() as directory:
            bashrc = Path(directory) / ".bashrc"
            bashrc.write_text(original)
            environment = dict(os.environ, HOME=directory)
            manager = PROJECT / "scripts/manage-bashrc.py"

            def run(action, expected=0):
                result = subprocess.run(
                    [sys.executable, str(manager), action], env=environment,
                    capture_output=True, text=True, check=False
                )
                self.assertEqual(result.returncode, expected, result.stderr)

            run("install")
            run("install")
            self.assertEqual(bashrc.read_text().count("# >>> lightqv"), 1)
            run("check")
            content = bashrc.read_text()
            bashrc.write_text(content.replace("[[ -r", "# changed\n[[ -r"))
            run("remove", 1)
            bashrc.write_text(content)
            run("remove")
            run("remove")
            run("absent")
            self.assertEqual(bashrc.read_text(), original)

    def test_interactive_sudo_uses_gui_only_on_cyberpunk(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            theme = home / ".local/state/omarchy/current/theme.name"
            theme.parent.mkdir(parents=True)
            theme.write_text("cyberpunk\n")
            askpass = home / "Projects/omarchy-cyberpunk/askpass/cyberpunk-askpass"
            askpass.parent.mkdir(parents=True)
            askpass.write_text("#!/usr/bin/bash\nexit 0\n")
            askpass.chmod(0o700)
            bin_dir = home / "bin"
            bin_dir.mkdir()
            fake_sudo = bin_dir / "sudo"
            fake_sudo.write_text('#!/usr/bin/bash\nprintf "%s|%s\\n" "$*" "${SUDO_ASKPASS-}" >> "$TEST_LOG"\n')
            fake_sudo.chmod(0o700)
            log = home / "sudo-invocations"
            env = dict(os.environ, HOME=directory, WAYLAND_DISPLAY="wayland-test", TEST_LOG=str(log))
            env["PATH"] = f"{bin_dir}:/usr/bin"
            script = f"source {shlex.quote(str(PROJECT / 'scripts/interactive-sudo.sh'))}; sudo -v; sudo -n true; sudo -S -v"

            def run():
                master, slave = pty.openpty()
                try:
                    result = subprocess.run(
                        ["/usr/bin/bash", "--noprofile", "--norc", "-ic", script],
                        stdin=slave, stdout=slave, stderr=slave, env=env,
                        timeout=5, check=False
                    )
                    self.assertEqual(result.returncode, 0)
                finally:
                    os.close(slave)
                    os.close(master)

            run()
            lines = log.read_text().splitlines()
            self.assertEqual(lines[0], f"-A -v|{askpass}")
            self.assertEqual(lines[1:], ["-n true|", "-S -v|"])
            theme.write_text("osaka-jade\n")
            run()
            self.assertEqual(log.read_text().splitlines()[3:], ["-v|", "-n true|", "-S -v|"])


if __name__ == "__main__":
    unittest.main()
