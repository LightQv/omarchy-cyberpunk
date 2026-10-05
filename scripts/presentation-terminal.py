#!/usr/bin/env python3
"""Show controlled logo or real status output in an ordinary demo terminal."""

from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
mode = sys.argv[1]
print('\033[2J\033[H\033[?25l', end='', flush=True)
if mode == 'logo':
    text = (root / 'install.sh').read_text()
    logo = text.split("cat <<'LOGO'\n", 1)[1].split('\nLOGO', 1)[0]
    print('\033]0;Cyberpunk // Logo\007\033[38;2;83;227;210m' + logo + '\033[0m\n\n  OMARCHY CYBERPUNK\n', flush=True)
elif mode == 'status':
    print('\033]0;Cyberpunk // Component Status\007', end='', flush=True)
    subprocess.run([str(Path.home() / '.local/bin/cyberpunk'), 'status'], check=True)
else:
    raise SystemExit('Use logo or status')
try:
    time.sleep(300)
finally:
    print('\033[?25h', end='', flush=True)
