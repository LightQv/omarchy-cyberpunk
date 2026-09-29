"""The shared wordmark must react to palette edits without a rectangular halo."""

import importlib.util
import json
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


class LoginArtTest(unittest.TestCase):
    def test_shared_wordmark_is_transparent_and_palette_derived(self):
        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("login_art", str(root / "scripts/render-login-art"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp / "theme").mkdir()
            (temp / "theme/colors.toml").write_text((root / "theme/colors.toml").read_text())
            (temp / "theme/login-layout.json").write_text((root / "theme/login-layout.json").read_text())
            source = Image.new("RGBA", (800, 188))
            ImageDraw.Draw(source).rectangle((180, 80, 620, 100), fill="white")
            source.save(temp / "source.png")
            module.ROOT = temp
            module.SOURCE = temp / "source.png"
            module.GREETER = temp / "sddm-theme"
            module.BOOT = temp / "plymouth-theme"
            first = module.render_images()
            logo = first[module.BOOT / "logo.png"]
            self.assertEqual(logo.tobytes(), first[module.GREETER / "logo.png"].tobytes())
            self.assertEqual(logo.getpixel((0, 0))[3], 0)
            self.assertGreater(logo.getpixel((272, 162))[3], 0)
            colors = (temp / "theme/colors.toml").read_text()
            (temp / "theme/colors.toml").write_text(colors.replace('cyan = "#53e3d2"', 'cyan = "#43d3c2"'))
            changed = module.render_images()[module.BOOT / "logo.png"]
            self.assertNotEqual(logo.getpixel((272, 162)), changed.getpixel((272, 162)))

    def test_boot_prompt_and_progress_use_lock_field_geometry(self):
        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("boot_preview", str(root / "scripts/preview-login-art"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        layout = json.loads((root / "theme/login-layout.json").read_text())
        prompt = module.frame()
        progress = module.frame(0.62)
        scale, prompt_x, prompt_y, _ = module.geometry(prompt.width, prompt.height)
        self.assertEqual(prompt.size, (1920, 1080))
        self.assertEqual(scale, 0.75)
        self.assertAlmostEqual(prompt_x, 791.0, delta=1)
        self.assertAlmostEqual(prompt_y, 500.25, delta=1)
        field_x = round(prompt_x + (layout["promptWidth"] - layout["fieldWidth"]) / 2 * scale)
        field_y = round(prompt_y + layout["fieldY"] * scale)
        self.assertAlmostEqual(field_x, 817, delta=1)
        self.assertAlmostEqual(field_y, 604, delta=1)
        self.assertGreaterEqual(prompt.getpixel((field_x, field_y + 6))[0], 250)
        self.assertNotEqual(progress.getpixel((field_x, field_y + 6)), (255, 48, 69))
        self.assertGreater(prompt.getpixel((field_x + 60, round(prompt_y + layout["buttonY"] * scale)))[0], 180)
        bar = progress.getpixel((field_x + 80, field_y + round(layout["fieldHeight"] / 2 * scale)))
        self.assertGreater(bar[1], bar[0])
        self.assertEqual(prompt.getpixel((640, 180)), progress.getpixel((640, 180)))

    def test_wordmark_remains_prominent_without_overshadowing_form(self):
        root = Path(__file__).resolve().parents[1]
        layout = json.loads((root / "theme/login-layout.json").read_text())
        with Image.open(root / "plymouth-theme/logo.png") as logo:
            bbox = logo.convert("RGBA").getchannel("A").point(lambda alpha: 255 if alpha > 150 else 0).getbbox()
            letter_width = (bbox[2] - bbox[0]) * layout["logoWidth"] / logo.width
        self.assertGreater(letter_width, 1.55 * layout["promptWidth"])
        self.assertLess(letter_width, 1.8 * layout["promptWidth"])

    def test_logo_fault_settles_and_does_not_change_the_prompt(self):
        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("boot_fault", str(root / "scripts/preview-login-art"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        settled, opening = module.frame(), module.frame(logo_tick=0)
        self.assertIsNotNone(ImageChops.difference(opening.crop((540, 210, 1380, 450)),
                                                 settled.crop((540, 210, 1380, 450))).getbbox())
        self.assertEqual(opening.crop((790, 500, 1130, 740)).tobytes(),
                         settled.crop((790, 500, 1130, 740)).tobytes())
        self.assertEqual(module.frame(logo_tick=sum(module.art_recipe.LOGO_HOLDS)).tobytes(), settled.tobytes())

    def test_logo_fault_fragments_are_localized_and_shared(self):
        root = Path(__file__).resolve().parents[1]
        with Image.open(root / "plymouth-theme/logo.png") as original:
            base = original.convert("RGBA")
        for index in range(7):
            with Image.open(root / "plymouth-theme" / f"logo-fault-{index}.png") as boot:
                with Image.open(root / "sddm-theme" / f"logo-fault-{index}.png") as greeter:
                    self.assertEqual(boot.tobytes(), greeter.tobytes())
                diff = ImageChops.difference(base, boot.convert("RGBA"))
            self.assertIsNotNone(diff.getbbox())
            pixels = diff.load()
            widest_row = max(sum(any(pixels[x, y][:3]) for x in range(base.width))
                             for y in range(base.height))
            self.assertLess(widest_row, base.width * .35)

    def test_some_fault_sparks_escape_the_letter_silhouette(self):
        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("horizontal_sparks", str(root / "scripts/render-login-art"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        recipe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recipe)
        with Image.open(root / "plymouth-theme/logo.png") as original:
            clean = original.convert("RGBA")
        visible = clean.getchannel("A").point(lambda alpha: 255 if alpha > 150 else 0).getbbox()
        for frame in recipe.fault_sparks(visible):
            self.assertTrue(all(y1 == y2 for _, y1, _, y2 in frame))
        outside = Image.new("L", clean.size, 255)
        ImageDraw.Draw(outside).rectangle(visible, fill=0)
        for index in range(7):
            with Image.open(root / "plymouth-theme" / f"logo-fault-{index}.png") as image:
                changed = ImageChops.difference(image.convert("RGBA"), clean).getchannel("A")
                escaped = ImageChops.multiply(changed, outside).getbbox()
                self.assertIsNotNone(escaped)
                self.assertTrue(escaped[0] < visible[0] - 18 or escaped[1] < visible[1] - 18
                                or escaped[2] > visible[2] + 18 or escaped[3] > visible[3] + 18)
                self.assertGreater(escaped[0], 0)
                self.assertGreater(escaped[1], 0)
                self.assertLess(escaped[2], clean.width)
                self.assertLess(escaped[3], clean.height)

    def test_boot_masks_replace_placeholder_without_changing_frame(self):
        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader("boot_masks", str(root / "scripts/preview-login-art"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plain, masked = module.frame(), module.frame(bullets=7)
        scale, prompt_x, prompt_y, _ = module.geometry(plain.width, plain.height)
        field_x = round(prompt_x + (module.LAYOUT["promptWidth"] - module.LAYOUT["fieldWidth"]) / 2 * scale)
        field_y = round(prompt_y + module.LAYOUT["fieldY"] * scale)
        changed = ImageChops.difference(plain, masked).crop((field_x + 30, field_y + 5,
                                                               field_x + 160, field_y + 37))
        self.assertIsNotNone(changed.getbbox())
        self.assertEqual(plain.getpixel((960, 240)), masked.getpixel((960, 240)))

    def test_plymouth_sprite_offsets_match_shared_lock_layout(self):
        root = Path(__file__).resolve().parents[1]
        layout = json.loads((root / "theme/login-layout.json").read_text())
        script = (root / "plymouth-theme/lightqv-cyberpunk.script").read_text()
        for line in (
            f'entry.width = {layout["fieldWidth"]} * entry.scale;',
            f'logo.width = {layout["logoWidth"]} * entry.scale;',
            f'prompt.scale = {layout["baseScale"]};',
            f'width_scale = {layout["baseScale"]} * Window.GetWidth() / {layout["referenceWidth"]};',
            f'height_scale = {layout["baseScale"]} * Window.GetHeight() / {layout["referenceHeight"]};',
            f'prompt.x = (Window.GetWidth() - {layout["promptWidth"]} * prompt.scale) / 2;',
            f'entry.y = prompt.y + {layout["fieldY"]} * entry.scale;',
            f'action.sprite.SetPosition(entry.x, prompt.y + {layout["buttonY"]} * entry.scale, 10001);',
            f'hint.sprite.SetPosition(entry.x, prompt.y + {layout["hintY"]} * entry.scale, 10001);',
        ):
            self.assertIn(line.strip(), script)
        self.assertIn('hide_password_dialog();', script)
        self.assertIn('progress_box.sprite.SetOpacity(1);', script)
        self.assertIn('Plymouth.SetBootProgressFunction(progress_callback);', script)


if __name__ == "__main__":
    unittest.main()
