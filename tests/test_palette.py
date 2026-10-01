"""An isolated one-color edit must reach Omarchy's derived theme outputs."""

import importlib.util
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


class PaletteTest(unittest.TestCase):
    def test_cyan_edit_updates_ansi_shell_and_auth_preview(self):
        project = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("cyberpunk_palette", str(project / "scripts/render-palette"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory) / "theme"
            preview = Path(directory) / "lock-plugin"
            theme.mkdir()
            preview.mkdir()
            for name in ("colors.toml", "shell.toml"):
                (theme / name).write_text((project / "theme" / name).read_text())
            (preview / "PreviewPalette.js").write_text((project / "lock-plugin/PreviewPalette.js").read_text())

            module.COLORS = theme / "colors.toml"
            module.SHELL = theme / "shell.toml"
            module.PREVIEW = preview / "PreviewPalette.js"
            original = module.COLORS.read_text()
            module.COLORS.write_text(original.replace('cyan = "#53e3d2"', 'cyan = "#43d3c2"'))
            outputs = module.render()
            self.assertIn('bright_cyan = "#98efe2"', outputs[module.COLORS])
            self.assertIn('border = "#43d3c2"', outputs[module.SHELL])
            self.assertIn('var cyan = "#43d3c2"', outputs[module.PREVIEW])

            module.COLORS.write_text(original.replace('red = "#ff3045"', 'red = "#ef2035"'))
            outputs = module.render()
            self.assertIn('accent = "#ef2035"', outputs[module.COLORS])
            self.assertIn('hyprland_active_border = "rgba(ef2035ff)', outputs[module.COLORS])
            self.assertIn('active = "#ef2035"', outputs[module.SHELL])
            self.assertIn('var red = "#ef2035"', outputs[module.PREVIEW])


if __name__ == "__main__":
    unittest.main()
