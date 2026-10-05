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

https://github.com/user-attachments/assets/2f13bbd8-1528-4b66-b1b4-9676b275b185

[Full-quality continuous presentation — 60 seconds, 2560×1440, 60 FPS](presentation.mp4).
It starts on wallpaper 06, browses the menu/submenu and searches for Ghostty, shows
the installer logo and real component status at normal terminal font size, switches
focus and scheme, steps through the wallpaper carousel to 11, then shows one
private sample notification, gradual volume/mute/unmute OSD and real Polkit
failure/retry/success. Passwords were entered directly into masked dialogs; no
credential values were logged. Audio and mouse pointer are excluded.

The full-quality MP4 is stream-copied without cuts or re-encoding. The inline GitHub
attachment is a 7.19 MB H.264, two-pass 950 kbit/s copy made to fit GitHub's 10 MB
free-plan upload limit. It preserves the complete 60.15-second take, 1440p and 60 FPS.

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
python -B scripts/presentation.py --rehearse --take rehearsal1 # No auth prompts
python -B scripts/presentation.py --take organic              # User participation
python -B scripts/export-presentation --take organic          # After reviewing footage
```

The controller uses an empty workspace and restores workspace, wallpaper, scheme
and DND afterward. Sample notifications run on a private HOME/bus; actual audio
settings are untouched. Polkit authenticates only `/usr/bin/true`, making no
privileged system changes. It waits up to 150 seconds for failure/retry/success,
then aborts and cleans up on failure. Take files are not overwritten; an
optional `--take NAME` suffix is available for retries. Raw recordings, logs and
rehearsals remain ignored under `showcase/presentation/`.

The terminal content helper is `scripts/presentation-terminal.py`; no font-size
override is used. Menu/carousel movement and typed search use paced keyboard input.

`capture-desktop` briefly selects wallpaper `11.png` and an unused workspace,
captures the actual top bar with no open windows, then restores the original
wallpaper and workspace even if capture fails. Run while unlocked, with no popups,
notifications or authentication dialogs. The resulting bar reflects your setup;
visually inspect the image before publishing it.
