"""Exercise the real preview and terminal prompts without downloading/installing."""

import errno
import fcntl
import os
from pathlib import Path
import pty
import struct
import subprocess
import tempfile
import termios
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerPreviewTest(unittest.TestCase):
    def terminal_preview(self, *options, answers=b'', width=80, no_color=False):
        with tempfile.TemporaryDirectory() as directory:
            master, slave = pty.openpty()
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, width, 0, 0))
            environment = dict(os.environ, HOME=directory, TERM='xterm-256color',
                               COLORTERM='truecolor', LC_ALL='C.UTF-8', PYTHONDONTWRITEBYTECODE='1')
            for key in ('COLUMNS', 'LINES', 'NO_COLOR'):
                environment.pop(key, None)
            if no_color:
                environment['NO_COLOR'] = ''
            def session():
                os.setsid()
                fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
            process = subprocess.Popen(['bash', str(ROOT / 'dev'), 'preview', 'installer', *options],
                                       stdin=subprocess.PIPE, stdout=slave, stderr=slave,
                                       env=environment, preexec_fn=session)
            os.close(slave)
            if answers:
                os.write(master, answers)
            # Standard input is not the terminal (just like curl | bash).
            process.stdin.write(b'this is script input, not setup answers\n')
            process.stdin.close()
            try:
                process.wait(timeout=15)
                output = bytearray()
                while True:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError as error:
                        if error.errno == errno.EIO:
                            break
                        raise
                    if not chunk:
                        break
                    output.extend(chunk)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                os.close(master)
            self.assertEqual(list(Path(directory).iterdir()), [], 'Preview wrote user files')
            return process.returncode, output.decode().replace('\r\n', '\n')

    def test_menu_and_custom_answers_use_tty_not_script_input(self):
        code, output = self.terminal_preview(answers=b'3\ny\nn\ny\nn\ny\ny\ny\n')
        self.assertEqual(code, 0, output)
        self.assertIn('Choose your Cyberpunk setup', output)
        self.assertIn('Requested setup: menu, osd, polkit, lock', output)
        self.assertIn('Native — safe mode; preference enabled', output)
        self.assertIn('\x1b[38;2;83;227;210m', output)

    def test_base_default_and_no_color(self):
        code, output = self.terminal_preview(answers=b'\n\n', no_color=True)
        self.assertEqual(code, 0, output)
        self.assertIn('base theme only', output)
        self.assertNotIn('\x1b', output)

    def test_full_noninteractive_preview_and_narrow_fallback(self):
        code, output = self.terminal_preview('--setup', 'full', '--non-interactive', width=60)
        self.assertEqual(code, 0, output)
        self.assertIn('preference enabled', output)
        self.assertNotIn('⣀⡀', output)
        self.assertNotIn('Selection [1]', output)

    def test_cancel_does_not_simulate_installation(self):
        code, output = self.terminal_preview(answers=b'1\nn\n')
        self.assertNotEqual(code, 0, output)
        self.assertIn('Setup cancelled', output)
        self.assertNotIn('Installing… (simulated)', output)
