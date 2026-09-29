"""SDDM selects its Qt major version from each theme's metadata."""

import configparser
import unittest
from pathlib import Path


class SddmMetadataTest(unittest.TestCase):
    def test_themes_match_stock_omarchy_qt_version(self):
        root = Path(__file__).resolve().parents[1]
        files = [
            Path("/usr/share/sddm/themes/omarchy/metadata.desktop"),
            root / "sddm-theme/metadata.desktop",
            root / "sddm-selector/metadata.desktop",
        ]
        versions = []
        for path in files:
            with self.subTest(theme=path):
                config = configparser.ConfigParser()
                self.assertTrue(config.read(path), f"missing SDDM metadata: {path}")
                versions.append(config["SddmGreeterTheme"].get("QtVersion"))
        self.assertEqual(versions, ["6", "6", "6"])


if __name__ == "__main__":
    unittest.main()
