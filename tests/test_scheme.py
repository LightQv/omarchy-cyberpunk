"""Check semantic interface inversion while preserving ANSI palette and text roles."""

from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from scheme import render


class SchemeTest(unittest.TestCase):
    def test_inversion_changes_interface_roles_not_terminal_palette(self):
        base = {name: (ROOT / 'theme' / name).read_text() for name in ('colors.toml', 'shell.toml')}
        output = render(base, 'inverted')
        old, new = (tomllib.loads(value) for value in (base['colors.toml'], output['colors.toml']))
        for key in ('red', 'cyan', 'blue', 'green', 'yellow', 'foreground', 'background', 'bright_red', 'bright_cyan'):
            self.assertEqual(new[key], old[key], key)
        self.assertEqual(new['accent'], old['cyan'])
        self.assertIn(old['cyan'][1:], new['hyprland_active_border'])
        shell = tomllib.loads(output['shell.toml'])
        self.assertEqual(shell['lock']['border'], old['red'])
        self.assertEqual(shell['lock']['border-active'], old['cyan'])
        self.assertEqual(shell['polkit']['accent'], old['cyan'])
        self.assertEqual(shell['polkit']['border'], old['red'])
        self.assertEqual(shell['controls']['focus-color'], old['red'])
        self.assertEqual(shell['controls']['selected-color'], old['cyan'])
        self.assertEqual(shell['menu']['text'], old['foreground'])
        self.assertEqual(render(base, 'default'), base)
