# Provenance

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
- `theme/backgrounds/01-lucy.png`: the user's requested Lucy/Night City image
  from [CyberArch-Shell `assets/img/lucy_wallpaper.png`](https://github.com/ARCANGEL0/CyberArch-Shell/blob/master/assets/img/lucy_wallpaper.png),
  1672×941. The upstream project declares no image redistribution license.
  Kept on this machine only and excluded from Git; the project's download helper
  records its source and exact checksum without claiming redistribution rights.
- `theme/backgrounds/03-night-city.jpg`: CD PROJEKT RED's [official Phantom
  Liberty screenshot](https://cdn-l-cyberpunk.cdprojektred.com/cyberpunk2077/phantom-liberty/gallery-screenshot-03@2x.jpg),
  2270×1280. CDPR's fan-content guideline explicitly discusses turning game
  screenshots into wallpapers. Kept on this machine and excluded from Git.
- `theme/preview.png`: a derived thumbnail of the local Lucy artwork; also
  excluded from Git. `scripts/fetch-wallpapers` reproducibly prepares the two
  sources for personal use when missing.
- `theme/colors.toml` and `theme/shell.toml`: original red/turquoise palette and
  styles; no copyrighted game assets are included.
- No CyberArch-Shell code or assets are tracked or distributed. Its public
  repository has no declared license; its menu is only a visual reference.

This is unofficial fan-made artwork, not endorsed by CD PROJEKT RED.
