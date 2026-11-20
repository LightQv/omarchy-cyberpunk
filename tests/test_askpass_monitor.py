"""Place askpass on the focused Hyprland monitor, not Qt's primary screen."""

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("askpass", ROOT / "askpass/askpass.py")
askpass = importlib.util.module_from_spec(spec)
spec.loader.exec_module(askpass)

MONITORS = [
    {"name": "DP-2", "focused": False},
    {"name": "DP-3", "focused": True},
]


def completed(stdout: bytes) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr=b"")


class FocusedOutputTest(unittest.TestCase):
    def test_returns_focused_hyprland_monitor(self):
        with patch.object(askpass.subprocess, "run",
                          return_value=completed(json.dumps(MONITORS).encode())):
            self.assertEqual(askpass.focused_output(), "DP-3")

    def test_falls_back_when_hyprctl_is_unavailable(self):
        with patch.object(askpass.subprocess, "run", side_effect=FileNotFoundError):
            self.assertIsNone(askpass.focused_output())

    def test_falls_back_on_invalid_output(self):
        with patch.object(askpass.subprocess, "run", return_value=completed(b"not json")):
            self.assertIsNone(askpass.focused_output())

    def test_capture_is_limited_to_focused_output(self):
        calls = []

        def fake_run(args, **_kwargs):
            calls.append(args)
            if args[0] == "hyprctl":
                return completed(json.dumps(MONITORS).encode())
            return completed(b"")

        env = {"WAYLAND_DISPLAY": "wayland-1", "QT_QPA_PLATFORM": "wayland"}
        with patch.dict(askpass.os.environ, env), \
                patch.object(askpass.subprocess, "run", side_effect=fake_run):
            askpass.Askpass._capture_desktop()
        grim = next(call for call in calls if call[0] == "grim")
        self.assertEqual(grim[grim.index("-o") + 1], "DP-3")


if __name__ == "__main__":
    unittest.main()
