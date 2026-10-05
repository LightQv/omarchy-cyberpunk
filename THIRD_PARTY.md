# Provenance

The upstream package baseline, original paths, copied-file mappings and SHA-256
hashes are recorded in `scripts/omarchy-baseline.json`. See
`docs/COMPATIBILITY.md` for source auditing and new-release acceptance.

- `menu-plugin/Menu.qml`, `MenuModel.js`, `BarWidget.qml`: copied from the
  installed Omarchy 4.0.4-1 menu plugin and modified under Omarchy's MIT
  license; its copyright and license notice are retained in `LICENSE`.
- `menu-plugin/LocalAppLibrary.qml` and `AppSearch.js`: copied from Omarchy
  4.0.4-1 to retain its desktop-entry discovery, hidden-entry filtering,
  icon lookup, and launch/remove behavior in a third-party menu clone.
- `polkit-plugin/PolkitAgent.qml`, `PolkitModel.js`: copied from the installed
  Omarchy 4.0.4-1 authentication plugin and given a new presentation while
  preserving the original Polkit/PAM flow. The Omarchy MIT notice is in `LICENSE`.
- `notifications-plugin/Service.qml`, `NotificationLogic.js`, and
  `components/NotificationCard.qml`: copied from Omarchy 4.0.4-1 under its MIT
  license. The clone preserves delivery, DND, history, actions, and dismissal;
  only the card presentation and placement have been changed.
- `osd-plugin/OsdModel.js` and the OSD IPC in `Osd.qml`: derived from Omarchy
  4.0.4-1 under its MIT license. The display has been restyled while retaining
  its native payload parsing, status types, and timer behavior.
- `askpass/askpass.py`, the Bash integration, and the red/turquoise authentication
  layout are original. They require the already-installed PySide6 package.
- `theme/backgrounds/01.png` through `13.png`: generated wallpapers supplied by
  the project author from their local `Documents/cyberpunk_wallpapers` collection.
  Original files are included without resizing or recompression, each 1672×941.
  Numbering defines the picker order; `01.png` is the default artwork. These
  replace the former CyberArch Lucy image and official CDPR screenshot placeholders.
- `theme/preview.png`: a bundled 900×506 thumbnail derived from `01.png`.
- `docs/media/`: curated current component captures and offline auth appearance
  demos using the author's `06`, `07`, `09`, `10` and `12` wallpapers. Desktop
  captures use the actual component QML and illustrative messages/shortcut rows
  in a private preview session. Auth demos do not register PAM/Polkit services or
  use real credentials. The media manifest records inputs and published hashes.
- `theme/colors.toml` and `theme/shell.toml`: original red/turquoise palette and
  styles; no copyrighted game assets are included.
- `lock-plugin/Service.qml` and `StockLockView.qml`: generated from the pinned
  installed Omarchy 4.0.4-1 lock under its MIT license; the generator rejects
  unreviewed upstream authentication changes.
- No CyberArch-Shell code or assets are tracked or distributed. Its public
  repository has no declared license; its menu is only a visual reference.

This is unofficial fan-made artwork, not endorsed by CD PROJEKT RED.
