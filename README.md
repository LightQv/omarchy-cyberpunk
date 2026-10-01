# Omarchy Cyberpunk

A red/turquoise desktop theme for **Omarchy 4.0.4-1**, with a curved HUD menu,
warning-style notifications, centered action OSDs, and matching session-lock,
sudo and Polkit presentation.

**Boot/disk unlock and SDDM login are managed by Omarchy.** Desktop theme changes
do not select a boot theme, rebuild UKIs, install a privileged watcher, or change
the display manager. Omarchy's native Unlock styling remains independent.

## Readiness

This is a development checkout, not yet a verified clean-install release.
The desktop theme and sudo/Polkit presentation have passed live review and real
authentication. The current custom session lock has also passed a supervised
manual unlock and wrong-password retry, with user-accepted input and presentation.
Repeated unlock, secure deferred restoration and the normal uninstall/reinstall
cycle also passed. Native missing-link recovery, supervised wallpaper fallback,
idle locking and display blank/wake now pass too. Portable baseline creation and
relocated-checkout sudo routing have isolated first-install coverage. A pristine
user/machine install and broader hardware cases remain release qualifications;
the shared suspend-focus limitation below keeps lock safe mode on with
`omarchy.lock` active.
See the authoritative
[roadmap](LOGIN-LOCK-PALETTE-OSD-PLAN.md) for accepted results and remaining gates.

## Components

| Component | Presentation |
| --- | --- |
| Desktop | Local Lucy/Night City backgrounds, palette-derived shell colors and directional red window borders. |
| Menu | Curved command/App rows, search, stable hover, wheel scrolling and mirrored Keybindings. Native routes and caller semantics retained. |
| Notifications | Pulsing warning icon, stepped joined border, wrapping message reveal and reverse dismissal. Native delivery/DND/history/actions retained. |
| OSD | Turquoise volume, red mute and centered non-progress action messages. Native brightness/media/microphone payloads retained. |
| Sudo/Polkit | Frozen/dimmed backdrop, beveled masks, one padded red caret and matching cut-corner action. Shared glitch effect repeats while visible. |
| Session lock | Pinned native authentication service with custom backdrop/prompt and a brief settling effect. Changes defer while a secure lock is active. |

Sudo/Polkit shuffle whole 0.85/1.10/1.40-second sequences with independently varied
350–800 ms pauses. `OMARCHY_REDUCED_MOTION=1` suppresses their cosmetic loops.
Captured desktop imagery is local/private; credentials are never sent through
shell IPC or written into captures or diagnostic files.

## Development installation

Dependencies include Omarchy's Quickshell/Qt 6 environment, Python/PySide6, Bash,
`jq`, `flock`, and `grim`. Offline previews also require Pillow and FFmpeg.
The lock generator is pinned to the inspected Omarchy release and refuses
unreviewed upstream authentication changes.

1. Review `THIRD_PARTY.md`. Prepare personal-use artwork with
   `scripts/fetch-wallpapers`; artwork and derived previews are Git-ignored.
2. First installation creates a private baseline snapshot at
   `~/.local/state/omarchy-cyberpunk-backup/{shell.json,bashrc,modes.json}`.
   Existing complete baselines are retained unchanged. An incomplete or symlinked
   baseline is refused; preserve it elsewhere before retrying. No private baseline
   from the development machine is required. The checkout can live at an arbitrary
   absolute path, including one containing spaces. Keep it in place while installed.
3. Review the scripts and run from the checkout while unlocked:

   ```sh
   scripts/render-palette --check
   scripts/build-lock --check
   scripts/install-dev
   scripts/verify --check
   ```

Installation creates project-owned links for the theme and five shell plugins,
an exact interactive-Bash stanza, and `theme-set`/`post-boot` **desktop**
reconciliation hooks. The post-boot hook repairs interrupted desktop selection;
it does not change Plymouth, SDDM, initramfs or UKIs.
Fresh installation starts with the custom lock suppressed for live acceptance.

Omarchy theme selection may restart OpenCode. When installing through an agent,
use a one-shot user service if necessary, and inspect its exit status:

```sh
systemd-run --user --collect --unit=omarchy-cyberpunk-install "$PWD/scripts/install-dev"
systemctl --user show omarchy-cyberpunk-install.service -p Result -p ExecMainStatus
```

## Usage and lock control

Select Cyberpunk through Omarchy's normal desktop theme picker. Other desktop
themes restore stock menu, notifications, OSD, Polkit and lock presentation.
Use `scripts/verify --repair` to reconcile an interrupted switch.

```sh
scripts/lock-screen status
scripts/lock-screen enable
scripts/lock-screen disable
```

The saved preference affects only the session lock. Disabling it leaves the
desktop theme, sudo and Polkit active. `.state/safe-mode` suppresses the custom
lock until acceptance; it is no longer a three-screen boot/greeter switch.

For a supervised current-design lock trial:

```sh
scripts/lock-screen trial
# Manually lock, test authentication, then unlock.
scripts/lock-screen restore
```

These operations require an unlocked, PAM-ready session. Do not remove the
safe-mode file until the lock trial and lifecycle checks pass. No command above
automatically locks, logs out, or reboots the machine.

## Sudo and Polkit

Interactive Bash uses graphical askpass only when Cyberpunk is selected in a
Wayland terminal. Open a new terminal or source `~/.bashrc` to load the function.
Off-theme, scripted sudo, `sudo -n` and `sudo -S` retain native behavior.
The actual command is native `sudo -A`; only an accepted password reaches sudo
through askpass stdout.

Polkit retains its native agent/PAM flow. Only one agent should be active.
If a manual plugin change breaks registration, restore stock:

```sh
omarchy plugin disable lightqv.cyberpunk-polkit
omarchy plugin enable omarchy.polkit
```

## Palette and previews

Edit `theme/colors.toml`, then run `scripts/render-palette --write` before
reapplying the desktop theme. The renderer updates ANSI/shell roles and the
auth-preview palette. Sudo reads the active palette when opening.

```sh
python scripts/preview-final
python scripts/verify-final-previews
python -m unittest discover -s tests
scripts/build-lock --check
```

`preview/` contains **lock, sudo and Polkit** stills/clips. They cannot authenticate
or register secure surfaces and are not substitutes for live trials.

## Update, recovery and removal

After an Omarchy update, run `scripts/build-lock --check` and plugin validations
before custom lock activation. A pin mismatch requires upstream review.
Theme/preference transitions must preserve an active secure lock and defer
reconciliation until unlock rather than destroying its surface.

```sh
scripts/uninstall-dev
scripts/verify --removed
```

Removal restores native plugins and the recorded prior desktop theme, removes
only owned links and the exact Bash stanza, and retains personal imagery/source
and private backups. It does not restore whole shell/Bash configurations over
unrelated edits. A real active-theme uninstall, removal check, repeated uninstall
and reinstall passed, with unrelated shell/Bash settings, saved lock preference
and background preserved. A second native cycle recovered deliberately missing
menu/OSD links and preserved the original baseline. Ten isolated lifecycle tests
cover interrupted states, ownership conflicts, operation concurrency and clean
first-install snapshot creation. New-machine end-to-end installation remains a
release qualification. Missing owned links can be recovered by
rerunning `scripts/uninstall-dev`, followed by `scripts/install-dev`. Removal
temporarily rediscovers missing clones only when their configuration still needs
native restoration. Occupied foreign paths and edited sudo markers are refused.
Install/removal commands are serialized independently of theme reconciliation.
If another active clone now owns one of the native services, removal stops before
changing configuration rather than disabling that unrelated clone.

### Known suspend/resume limitation

After resume, password feedback required clicking the field in both the themed
lock and stock `omarchy.lock` on this machine. Authentication succeeded afterward.
The stock comparison indicates a shared issue rather than a custom-mask-only
regression; it does not establish the exact cause or whether earlier keystrokes
were retained. A tested speculative focus hook did not fix the live issue and was
removed. The theme retains native lock focus/secure-surface behavior, and this
limitation remains open pending resolution or explicit user acceptance.

This is separate from ordinary idle/display blanking: a supervised native idle
lock and DPMS off/on passed with first-key feedback and correct unlock. Original
idle/stay-awake settings were restored afterward. Controlled screensaver-class
wallpaper fallback also passed; native screensaver animation startup is not
claimed as accepted by that controlled check.

### Historical boot/login experiment

Boot/login support was retired, and installed-system cleanup is complete.
Its implementation, removal-only migration, tests and old documentation are
preserved outside the active checkout at
`~/Projects/omarchy-cyberpunk-archives/boot-login-retired-2026-10-01/`.
There is no boot/greeter migration or activation code in the desktop product.

See `THIRD_PARTY.md` and `LICENSE` for provenance. Unofficial fan-made project;
not affiliated with CD PROJEKT RED.
