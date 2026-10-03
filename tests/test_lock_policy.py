"""Lock-only preference and trial gates must not affect boot or greeter state."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LockPolicyTest(unittest.TestCase):
    def test_safe_mode_trial_and_preference(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            script = f'''source "{ROOT}/scripts/common.sh"
STATE_DIR="{state}"
SAFE_MODE="$STATE_DIR/safe-mode"
LOCK_PREF="$STATE_DIR/lock-preference"
LOCK_TRIAL="$STATE_DIR/lock-trial"
PREFERENCES="$STATE_DIR/no-preferences.json"
lock_enabled && lock_allowed
touch "$SAFE_MODE"
! lock_allowed
printf 'lock\\n' >"$LOCK_TRIAL"
lock_allowed
printf 'disabled\\n' >"$LOCK_PREF"
! lock_enabled
printf 'enabled\\n' >"$LOCK_PREF"
lock_enabled
printf 'greeter\\n' >"$LOCK_TRIAL"
! lock_allowed
'''
            result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_or_symlink_preference_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            pref = Path(directory) / "preference"
            pref.write_text("boot enabled\n")
            script = f'source "{ROOT}/scripts/common.sh"; PREFERENCES="{directory}/absent.json"; LOCK_PREF="{pref}"; lock_enabled'
            self.assertNotEqual(subprocess.run(["bash", "-c", script], capture_output=True).returncode, 0)
            pref.unlink()
            pref.symlink_to(ROOT / "README.md")
            self.assertNotEqual(subprocess.run(["bash", "-c", script], capture_output=True).returncode, 0)
