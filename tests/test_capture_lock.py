"""Capture must reject screensavers, fail safely and use a private fixed path."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CaptureLockTest(unittest.TestCase):
    def run_capture(self, clients, success):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bins = root / "bin"
            bins.mkdir()
            hypr = bins / "hyprctl"
            hypr.write_text('#!/bin/sh\nprintf "%%s\\n" \'%s\'\n' % clients)
            hypr.chmod(0o700)
            grim = bins / "grim"
            grim.write_text('#!/bin/sh\nprintf pixels > "$3"\nexit %s\n' % (0 if success else 1))
            grim.chmod(0o700)
            target = root / "lightqv-cyberpunk-lock.png"
            env = dict(os.environ, XDG_RUNTIME_DIR=str(root), PATH=str(bins) + ":" + os.environ["PATH"])
            result = subprocess.run([str(ROOT / "lock-plugin/capture-lock"), str(target)], env=env, capture_output=True)
            return result.returncode, target.exists(), (root / "lightqv-cyberpunk-lock.png.partial").exists(), (target.stat().st_mode & 0o777 if target.exists() else None)

    def test_screensaver_refused_and_failed_capture_leaves_no_image(self):
        self.assertEqual(self.run_capture('[{"class":"org.omarchy.screensaver"}]', True)[:3], (1, False, False))
        self.assertEqual(self.run_capture('[]', False)[:3], (1, False, False))

    def test_success_publishes_private_capture_and_no_partial(self):
        self.assertEqual(self.run_capture('[]', True), (0, True, False, 0o600))
