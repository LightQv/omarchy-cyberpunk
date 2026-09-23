# Omarchy Cyberpunk prototype

Omarchy 4.0.4-1 theme and theme-scoped menu clone. The on-demand curved
scanner presents the regular Omarchy command, system, and Apps routes
in the same red/turquoise HUD style. The original menu model still handles
routes, select/input callers, app launches, and the built-in bar button. A graphical
Polkit clone and Qt sudo askpass share the red/turquoise authentication style.
An Omarchy notifications clone draws one warning-style HUD toast centered near
the top, whether a menu is open or not. Its icon pulses twice; the third pulse
reveals the wrapping message from left to right, and dismissal reverses it.
The OSD clone styles the short-lived bottom-center volume bar in turquoise
(red when muted), while retaining the native brightness, microphone, media,
and status events. Focused windows get a directional red theme border.
The actual Omarchy lock screen remains the stock implementation. No background
service, Hyprland binding change, PAM/sudoers edit, or global shell replacement
is required. The Lucy scene is the primary wallpaper; an official CDPR Night
City screenshot provides a second background.

## Source and safety

The standalone theme is in `theme/`. The menu clone is in `menu-plugin/`, and
`scripts/install-dev` manages project-owned symlinks for the theme, menu,
Polkit agent, notifications service, and OSD, an exact `.bashrc` stanza,
and two event hooks
(`theme-set` and one-shot `post-boot` reconciliation). The source is stored in
a private GitHub repository; personal artwork remains local and Git-ignored.
The original `shell.json`, `.bashrc`, theme slug, and background link are backed
up outside this repo under `~/.local/state/omarchy-cyberpunk-backup/` (mode 700).

Artwork is local-only and ignored by Git. To prepare it on another machine,
review `THIRD_PARTY.md` and run `scripts/fetch-wallpapers` before installation.
The helper verifies each source checksum and never overwrites existing artwork.
Omarchy picks the first named image (`01-lucy.png`) when entering the theme from
another theme; its normal background cycling selects the alternative official
Night City screenshot. No HUD graphics are baked into either wallpaper.

Before activation, review `scripts/install-dev`, `scripts/uninstall-dev`, and
`scripts/verify`, then run:

```sh
omarchy plugin validate ~/Projects/omarchy-cyberpunk/menu-plugin
~/Projects/omarchy-cyberpunk/scripts/install-dev
~/Projects/omarchy-cyberpunk/scripts/verify --check
```

For an interrupted hook, run `scripts/verify --repair`. If upgrading an earlier
installed trial that did not include notifications, run
`scripts/upgrade-notifications` once while Cyberpunk is selected. For an earlier
trial without the volume OSD clone, run `scripts/upgrade-osd` once before
using `scripts/verify`; it installs only the owned OSD link and preserves the
currently selected theme. To remove the trial,
run `scripts/uninstall-dev` and then `scripts/verify --removed`; it restores
the built-in menu using Omarchy's API, switches back to the recorded theme if
needed, and unlinks only owned paths. The backup and project source remain.
Re-running uninstall after removal is safe, including after an interrupted
partial removal once the owned paths remain intact. It never restores the
entire `shell.json` or `.bashrc` and thus preserves unrelated edits made during
the trial. Uninstall deletes only the exact Bash stanza it installed.

Interactive Bash sessions use a `sudo` function that chooses the graphical
askpass only when Cyberpunk is selected and a Wayland terminal is present. The
function calls the real `sudo -A` with `SUDO_ASKPASS` pointing at the standalone
PySide6 UI. Outside Cyberpunk, or with `sudo -n` / `sudo -S`, it calls regular
sudo unchanged. Existing terminal sessions need `source ~/.bashrc` or a new
terminal to load the function. The password goes directly from askpass stdout
to sudo; no plaintext file, shell command argument, or shell IPC carries it.

Omarchy's theme command restarts OpenCode. When installing/removing from an
OpenCode session, run the script as a detached, one-shot user service:

```sh
systemd-run --user --collect --unit=omarchy-cyberpunk-trial ~/Projects/omarchy-cyberpunk/scripts/install-dev
systemctl --user show omarchy-cyberpunk-trial.service -p Result -p ExecMainStatus
```

The transient service is collected afterward; nothing keeps running.

Polkit and notifications each need one active D-Bus service. `scripts/verify
--repair` stops each stock service before starting its clone; switching themes
or uninstalling restores the stock services in the reverse order. If a manual
plugin toggle ever leaves authentication unavailable, run:

```sh
omarchy plugin disable lightqv.cyberpunk-polkit
omarchy plugin enable omarchy.polkit
```

After installing, check the menu button, `Super+Space`, `Super+Alt+Space`, and
`Super+Escape`, and a select/input caller before treating this as daily-ready.
See `THIRD_PARTY.md` for attribution. This is not affiliated with CD PROJEKT RED.

## Verified so far

- Plugin manifest and theme TOML parse; copied Omarchy menu data model is
  unchanged, and root/apps route calls and `ping` succeed in a live shell.
- Detached install and theme changes succeed; switching to Matte Black restores
  the built-in menu, and switching back enables the clone again.
- Uninstall from the active Cyberpunk theme succeeded and removed the owned
  plugin/theme links and both hooks. A temporary bar-transparency edit survived
  uninstall. After returning transparency to its original value, the JSON is
  semantically equal to the private backup (Omarchy reordered keys on save).
- Re-running uninstall when already removed exits successfully. Multi-monitor
  layout and login-time recovery still need hands-on testing before calling
  the menu production-ready.
- Askpass output/cancel behavior, theme-scoped interactive sudo dispatch, and
  byte-for-byte `.bashrc` install/remove round trip are covered by isolated
  tests. The Polkit clone registered in the live shell after the built-in
  agent stopped; switching away registered the built-in again. A fresh
  installation followed by removal while Cyberpunk was active restored
  Osaka Jade, the stock menu and agent, and the exact original `.bashrc`.
- The updated menu loads its own Omarchy-derived application library because
  the running host does not inject `shell.appLibrary` into the clone. Live
  calls enumerate the installed apps and preserve Omarchy icon and launch
  handling; root, Apps, and System routes retain their row counts. Keyboard
  navigation into a submenu and clearing search with Escape were checked on
  the live HUD. Select mode returned its requested choice and input mode
  returned typed text; both canceled cleanly. The visual layout merits review
  on your own display. The Lucy source is 1672×941, so it cannot contain native
  4K detail even on a 4K display.
- A shorter equal-width wheel, live list-index badges, layered red/turquoise
  glow, and eleven buffered slots avoid rebuilding delegates at every
  navigation step. The frames themselves roll vertically through the curve
  for single-step keyboard and wheel navigation; search, route changes, and
  reduced-motion mode snap directly. There is no opening slide. The two HUD
  separators are gone, and a labeled marker identifies extended search results.
  Index badges have opposite heavy edges on left and mirrored right wheels.
  The menu is slightly larger, with brighter neon
  outlines and both telemetry headings aligned to the wheel header. Keybindings
  select callers have a mirrored wheel on the right, index badges on the right,
  and telemetry on the left; other select
  callers keep their supplied width, search and return contracts. Notifications
  use the same centered banner with and without menus, retain Omarchy's native
  icon, summary, body, actions and history, and wrap long content vertically.
  Two warning pulses precede the third-pulse reveal; dismissal and expiry
  retract the panel before the row is removed. Opening and dismissal animations
  are skipped when reduced motion is requested.
  Osaka Jade → uninstall →
  reinstall → Cyberpunk passed with all three clones; a further Osaka Jade →
  Cyberpunk switch restored stock notifications off-theme and the HUD service
  on-theme. A further Osaka Jade → Cyberpunk check passed after the single-toast
  revision; a delivered toast was dismissed through normal notification IPC.
- The next pass gave the wheel eleven buffered slots. A live keypress showed a
  nonzero animation offset that settled to zero; Up wrapped from index 0 to 9,
  and three rapid Down presses reached index 2. The mirrored Keybindings view
  opened with eleven slots. Apps returned 48 entries, showed zero for an
  unmatched search, and restored all 48 after Escape. A volume, mute,
  brightness, and media OSD reached the stock `osd` IPC; a warning toast was
  delivered and dismissed through notification IPC. Plugin validation, QML
  syntax, Bash syntax, theme TOML, the three auth tests, and Hyprland config
  checks passed. Detached Osaka Jade → Cyberpunk and active-theme uninstall →
  reinstall trials passed with all four owned clones; the active border reports
  the configured 45° red gradient. Appearance on the user's display and
  multi-monitor/reduced-motion checks remain for visual acceptance.
- After display feedback, the row frames' horizontal curve is stronger on
  both wheels. The eleven-slot viewport is centered synchronously before the
  first paint and stays centered when changing between the main menu and
  Keybindings; the current shared intro fades the scrim, telemetry, and wheel
  together in 120 ms without a separate mirrored delay.
  Main-menu titles sit closer to their subtext, counts have a visible gap
  before chevrons, and the directional badge edges are subtler. The banner's
  warning triangle has even joins and a lower optical center for `!`, its
  leading bar spans the full height, and its title/body match the red border.
  Live root → Keybindings → Apps, ordinary select/input, keyboard wrap, and
  notification delivery/dismissal still worked without QML binding warnings.
- A further reference-image pass reduced the curve to a gentler 64 logical
  pixels on both wheels without changing the rolling transition. The warning
  triangle is now smaller than a default-height banner and has short, thicker
  strokes at its three angles; both stepped leading accents track the actual
  banner outline height, including wrapped messages. The volume OSD has no
  filled card or frame: its turquoise icon/label/percentage sit above a faint
  full-width track and a glowing filled bar with a slim white endpoint marker.
  Mute remains red; the same uncluttered surface handles stock brightness,
  media, microphone, and status messages. Live screenshots were inspected for
  the menu, banner, and volume bar; volume/mute/brightness/media IPC and
  notification dismissal responded normally.
- The Keybindings list and surrounding overlay now use the same short reveal,
  rather than drawing the background first. The warning triangle grew slightly;
  its lighter narrow stripe and stronger wide stripe are separate siblings
  painted above the banner frame, with a visible gap, both following the box's
  height. The full volume track and neon-filled portion are thicker; the active
  fill combines a turquoise glow and brighter core, while mute stays red.
  Live Keybindings, volume/mute, and a delivered/dismissed notification were
  checked after these changes.
- The latest adjustment softens the wheel curve from 64 to 52 logical pixels.
  The banner has a 4-pixel full-height left border, heavier than its other
  edges, and an equally thick outer line toward the triangle. The outer line
  starts 6 pixels below the border's top and ends 2 pixels before its bottom;
  they touch with no gap and grow with multiline banners.
  A live screenshot confirmed the joined edge; the root wheel reopened
  centered with eleven buffered slots.
- The left border and shorter outer line are now drawn as one stepped Canvas
  silhouette with a single pulse opacity. The panel no longer strokes its own
  left edge beneath that shape. Captures during a blink and after the reveal
  showed the same joined outline instead of independently fading stripes.
- The warning blinks now take 220 ms per half-pulse; two complete blinks
  precede the third-pulse panel reveal, which takes 550 ms. Dismissal retracts
  over 360 ms before a 160 ms icon fade; dismissing before the panel appears
  skips its empty retraction. Captures before and after reveal, a normal
  dismissal, and an early dismissal passed through notification IPC.
