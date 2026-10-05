# Showcase media

These captures use the current component code and the author's supplied wallpapers.

| View | Wallpaper | Capture |
| --- | --- | --- |
| Full desktop / top bar | `11.png` | Live Omarchy desktop on an empty workspace; author's actual bar configuration |
| Command menu / hero / menu motion | `06.png` | Actual menu QML in a private preview session |
| Apps / wallpaper picker | `07.png` | Actual menu and native image-picker QML |
| Keybindings | `09.png` | Actual select-menu QML, illustrative shortcut rows |
| Notifications | `10.png` | Actual notification service/cards, private D-Bus and sample messages |
| Volume / mute | `12.png` | Actual OSD QML, sample values |
| Session-lock appearance | `12.png` | Offline appearance scene; no secure surface or PAM |
| Sudo appearance | `09.png` | Actual askpass widget in non-authenticating offline mode |
| Polkit appearance / auth motion | `10.png` | Offline appearance scene; no agent registration |

Optional components are shown for demonstration. Fresh installation is base-only;
the custom lock remains safe-mode gated. The pictures do not contain real passwords,
user notification history or live authentication requests. Keybinding examples do
not install or redefine shortcuts.

The opening desktop capture includes the author's live top bar. Its layout and
third-party widgets are personal configuration, not installed by this theme.

## Motion

[Watch the continuous presentation — 73 seconds, 1920×1080, 60 FPS](presentation.mp4)
([release download](https://github.com/LightQv/omarchy-cyberpunk/releases/download/v0.1.4/presentation.mp4)).
It shows the live top bar, demo terminal borders, scheme inversion, menu/Apps,
wallpaper picker, private sample notifications, sample volume/mute OSD and real
sudo failure/retry/success followed by Polkit success. The user entered passwords
directly into masked dialogs; no credential values were logged. Audio and mouse
pointer are excluded. The exported MP4 is stream-copied, without cuts or re-encoding.

Compact GIFs are embedded in the main README. Full-resolution, silent H.264 clips:

- [Menu navigation — 1920×1080, 20 FPS](menu.mp4)
- [Lock appearance — 1920×1080, 50 FPS](lock.mp4)
- [Sudo appearance — 1920×1080, 50 FPS](sudo.mp4)
- [Polkit appearance — 1920×1080, 50 FPS](polkit.mp4)

`*-detail.png` files are cropped views for readable gallery cards. Full stills retain
the wider scene. Original wallpaper files remain unresized in `theme/backgrounds/`.

## Reproduce

From the checkout on the supported Omarchy release:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/preview-final \
  --lock-wallpaper 12.png --sudo-wallpaper 09.png --polkit-wallpaper 10.png
python scripts/verify-final-previews
PYTHONDONTWRITEBYTECODE=1 python scripts/preview-desktop
python scripts/export-showcase
PYTHONDONTWRITEBYTECODE=1 python scripts/capture-desktop
```

The desktop tool briefly covers the display with a clean preview wallpaper and
component windows. It uses a private HOME/session bus and terminates its windows
after capture. Run while unlocked, with no active authentication dialog.
Working renders remain ignored under `preview/` and `showcase/`.
`manifest.json` records artwork/source hashes and published asset hashes.

### Live presentation controller

```sh
python -B scripts/presentation.py --rehearse # Private technical take, no auth prompts
python -B scripts/presentation.py           # Real take: user participation required
python -B scripts/export-presentation       # Only after reviewing the footage
```

The controller uses an empty workspace and restores workspace, wallpaper, scheme
and DND afterward. Sample notifications run on a private HOME/bus; actual audio
settings are untouched. Sudo and Polkit authenticate only `/usr/bin/true`, making
no privileged system changes. It waits up to 150 seconds at each authentication
step, then aborts and cleans up on failure. Take files are not overwritten; an
optional `--take NAME` suffix is available for retries. Raw recordings, logs and
rehearsals remain ignored under `showcase/presentation/`.

`capture-desktop` briefly selects wallpaper `11.png` and an unused workspace,
captures the actual top bar with no open windows, then restores the original
wallpaper and workspace even if capture fails. Run while unlocked, with no popups,
notifications or authentication dialogs. The resulting bar reflects your setup;
visually inspect the image before publishing it.
