#!/usr/bin/env python3
"""Persist interface scheme and refresh shell/borders without theme-switch hooks."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

from preferences import DIRECTORY, trusted

ROOT = Path(__file__).resolve().parent.parent
STATE = DIRECTORY / "scheme.json"
BASE = DIRECTORY / "scheme-base.json"
THEME = ROOT / "theme"


def read():
    if not STATE.exists():
        return "default"
    trusted(STATE)
    data = json.loads(STATE.read_text())
    if data not in ({"version": 1, "scheme": "default"}, {"version": 1, "scheme": "inverted"}):
        raise ValueError("Invalid scheme preference")
    return data["scheme"]


def atomic(path, content):
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o600)
    temporary.replace(path)


def baseline(reset=False):
    if reset or not BASE.exists():
        data = {name: (THEME / name).read_text() for name in ("colors.toml", "shell.toml")}
        atomic(BASE, json.dumps(data))
    trusted(BASE)
    data = json.loads(BASE.read_text())
    release = ROOT / 'release.json'
    if release.exists():
        manifest = json.loads(release.read_text())['files']
        for name in ('colors.toml', 'shell.toml'):
            if hashlib.sha256(data[name].encode()).hexdigest() != manifest['theme/' + name]['sha256']:
                raise ValueError('Scheme base does not match the installed release')
    return data


def render(base, mode):
    colors, shell = base["colors.toml"], base["shell.toml"]
    if mode == "default":
        return {"colors.toml": colors, "shell.toml": shell}
    palette = tomllib.loads(colors)
    red, cyan = palette["red"], palette["cyan"]
    # Swap the two accent families, including renderer-derived variants, while
    # preserving unrelated background/text colors and all ANSI palette entries.
    def shifted(value, source, target):
        a = [int(source[i:i+2], 16) for i in (1, 3, 5)]
        b = [int(target[i:i+2], 16) for i in (1, 3, 5)]
        v = [int(value[i:i+2], 16) for i in (1, 3, 5)]
        return '#' + ''.join(f'{min(255, max(0, y + x - z)):02x}' for x, z, y in zip(v, a, b))
    mapping = {red: cyan, cyan: red}
    # Exact variants used by render-palette, reconstructed from semantic offsets.
    for source, target, offsets in ((red, cyan, ((0,19,22),)),
                                    (cyan, red, ((38,28,22), (85,28,32), (98,28,34)))):
        channels = [int(source[i:i+2], 16) for i in (1,3,5)]
        destination = [int(target[i:i+2], 16) for i in (1,3,5)]
        for delta in offsets:
            old = '#' + ''.join(f'{min(255,max(0,c+d)):02x}' for c,d in zip(channels,delta))
            new = '#' + ''.join(f'{min(255,max(0,c+d)):02x}' for c,d in zip(destination,delta))
            mapping[old] = new
    shell = re.sub(r'#[0-9a-fA-F]{6}', lambda match: mapping.get(match[0].lower(), match[0]), shell)
    colors = re.sub(r'(?m)^accent = ".*"$', f'accent = "{cyan}"', colors)
    selection = '#' + ''.join(f'{min(255,max(0,int(red[i:i+2],16)+d)):02x}' for i,d in zip((1,3,5),(-61,-172,-154)))
    colors = re.sub(r'(?m)^selection = ".*"$', f'selection = "{selection}"', colors)
    dark = shifted('#7b1c2b', red, cyan)
    colors = re.sub(r'(?m)^hyprland_active_border = ".*"$',
                    f'hyprland_active_border = "rgba({cyan[1:]}ff) rgba({dark[1:]}ff) 45deg"', colors)
    return {"colors.toml": colors, "shell.toml": shell}


def apply(reset=False):
    DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    trusted(DIRECTORY, directory=True)
    outputs = render(baseline(reset), read())
    for name, content in outputs.items():
        atomic(THEME / name, content)
    managed = ROOT / "managed.json"
    if managed.exists():
        trusted(managed)
        data = json.loads(managed.read_text())
        for name in outputs:
            data['directories']['theme'][name]['sha256'] = hashlib.sha256((THEME / name).read_bytes()).hexdigest()
        atomic(managed, json.dumps(data, indent=2) + '\n')


def refresh():
    current = Path.home() / '.local/state/omarchy/current'
    if (current / 'theme.name').read_text().strip() != 'cyberpunk':
        return
    for name in ('colors.toml', 'shell.toml'):
        atomic(current / 'theme' / name, (THEME / name).read_text())
    args = [base64.b64encode((THEME / name).read_bytes()).decode() for name in ('colors.toml', 'shell.toml')]
    subprocess.run(['omarchy-shell', 'shell', 'applyTheme', *args], check=True)
    hyprland = current / 'theme/hyprland.lua'
    palette = tomllib.loads((THEME / 'colors.toml').read_text())
    border = re.findall(r'rgba\([^)]+\)', palette['hyprland_active_border'])
    text, count = re.subn(r'(?m)^local active_border_color = .*$',
                         'local active_border_color = { colors = { ' + ', '.join('"' + color + '"' for color in border) + ' }, angle = 45 }', hyprland.read_text())
    if count != 1 or len(border) != 2:
        raise ValueError('Unsupported generated Hyprland border contract')
    atomic(hyprland, text)
    # Existing Lua theme configuration consumes generated border roles on reload.
    subprocess.run(['hyprctl', 'reload'], check=True)
    errors = subprocess.check_output(['hyprctl', 'configerrors'], text=True).strip()
    if errors and errors != 'ok':
        raise ValueError('Hyprland configuration errors: ' + errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('status', 'set', 'toggle', 'apply', 'reset-base', 'check'))
    parser.add_argument('value', nargs='?', choices=('default', 'inverted'))
    args = parser.parse_args()
    if args.action == 'status':
        print('Interface scheme: ' + read())
        return
    if args.action == 'check':
        if read() == 'inverted' and not BASE.exists():
            raise ValueError('Inverted scheme has no validated base palette')
        if BASE.exists():
            for name, content in render(baseline(), read()).items():
                if (THEME / name).read_text() != content:
                    raise ValueError('Scheme palette differs from saved scheme: ' + name)
        return
    if args.action in ('set', 'toggle'):
        layers = subprocess.check_output(['hyprctl', '-j', 'layers'], text=True)
        if 'omarchy-polkit' in layers or 'cyberpunk-askpass' in layers:
            raise ValueError('Finish active authentication dialogs before changing scheme')
        if args.action == 'set' and args.value is None:
            parser.error('set requires default or inverted')
        mode = args.value if args.action == 'set' else ('inverted' if read() == 'default' else 'default')
        previous = read()
        DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
        baseline()
        atomic(STATE, json.dumps({'version': 1, 'scheme': mode}) + '\n')
        try:
            apply()
            refresh()
        except BaseException:
            atomic(STATE, json.dumps({'version': 1, 'scheme': previous}) + '\n')
            apply()
            refresh()
            raise
        print('Interface scheme: ' + mode + ' (terminal ANSI colors unchanged)')
    else:
        apply(reset=args.action == 'reset-base')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('Cyberpunk: ' + str(error), file=sys.stderr)
        sys.exit(1)
