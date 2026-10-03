# Cyberpunk desktop, session lock, sudo and Polkit roadmap

## Product decision — October 1, 2026

**Boot/Plymouth and SDDM login support are retired from this product.** Omarchy
manages them independently of desktop theming. The product includes desktop
palette/wallpapers, menu, notifications, OSD, session lock, sudo and Polkit.
Keep native authentication, Omarchy picker integration and reversible user-owned
plugin changes. There is no three-screen preference matrix, custom UKI build,
privileged background boot reconciler or custom greeter selector in active source.

The former implementation and chronological plan/README are preserved outside
the checkout in `~/Projects/omarchy-cyberpunk-archives/boot-login-retired-2026-10-01/`.
This is a local historical snapshot, not dormant product functionality.

## Current authoritative checkpoint

### Public showcase checkpoint

Curated media under `docs/media/` uses `06` for menu/hero, `07` for Apps/picker,
`09` for Keybindings/sudo, `10` for notifications/Polkit and `12` for OSD/lock.
Actual desktop component QML was captured in a private HOME/session bus over a
clean wallpaper; shortcut rows/messages are illustrative. Auth renders remain
offline/non-authenticating. All three 1920×1080/50 FPS auth clips pass motion/settling
checks and now have source/artwork manifests. Public stills, detail crops, two GIFs
and four full-resolution clips replace the former placeholder-media presentation.

README uses a real component-render hero, gallery, motion and auth sections, a
wallpaper picker view, concise public CLI usage, and linked media reproduction
details. Working renders/logs stay ignored in `preview/` and `showcase/`. Preview
tooling no longer assumes an agent-specific `/tmp/opencode` directory.
The redundant legacy `preview-lock`/`Preview.qml` mock is removed; current auth
renders use the shared `preview-final`/`ReviewScene.qml` pipeline and manifest checks.

The current machine has no QEMU/libvirt tooling. A genuine pristine machine/user
session installation remains a stated development qualification; isolated HOME
tests use simulated native APIs and are not presented as clean-machine acceptance.
Publication is a development checkpoint, with stock lock safe mode preserved and
the shared suspend refocus issue documented.
The staged tracked-file export was checked independently: all 32 tests, the 20
public media/hash/link checks, palette/pin checks and CLI help pass without local
ignored assets/state. This verifies packaging completeness, not a pristine live
Omarchy user/session installation. Current desktop preferences and default wallpaper
remain preserved after preview capture.

### Persistent component CLI

Public interface: `cyberpunk --help`, `list`, `status`, `enable|disable <component|all>`, `check`,
`repair`, and `uninstall`. Components are menu, notifications, OSD (including volume),
sudo, Polkit and session lock. The installer owns a `~/.local/bin/cyberpunk` symlink.
Fresh installs select the Cyberpunk base palette/artwork with all six preferences
disabled. Existing installs migrate active Cyberpunk choices and the legacy lock
preference without resetting the current setup or clearing safe mode.

The private, versioned preferences file lives under XDG_STATE_HOME, defaulting to
`~/.local/state/omarchy-cyberpunk/preferences.json`. Updates are serialized and
atomic; preferences remain after uninstall/reinstall. Native themes always select
native components, and returning to Cyberpunk reapplies saved choices. Theme and
post-boot hooks, public repair and deferred lock restoration share the reconciler.
Help (`--help`, `-h`, `help`), `list`, `status` and `check` do not initialize or modify
state. `list` describes all six components and the `all` selector. Public lock toggles save the
choice while respecting safe mode and deferring active secure-surface changes.

32 isolated tests pass, including fresh base-only defaults, the installed command
from another working directory, six individual toggles, all on/off, saved mixed
theme round-trips, migration, retained preferences on reinstall, read-only status/
check, repair after failed activation, malformed/foreign-path protection and secure
deferred restoration. Sudo PTY tests cover enabled/disabled preference routing.
Live migration preserved the existing desktop selection: five components enabled,
lock preference enabled but native lock active under safe mode. The detached native
CLI check completed successfully: all six individual preference toggles and all
on/off passed; a mixed configuration survived Cyberpunk → matte-black → Cyberpunk
with native services selected off-theme and the exact mixture restored on return.
Original preferences/wallpaper, unrelated shell settings, Bash contents/mode and
stock-lock safe mode were preserved. Evidence:
`/tmp/opencode/cyberpunk-cli-live-result.json`, all comparisons true.

### Wallpaper and README checkpoint

The author-supplied generated collection is bundled as `theme/backgrounds/01.png`
through `13.png`, in filename order. All 13 originals decode at 1672×941 and match
their source checksums; `01.png` is the installation and preview default. The old
CyberArch Lucy/CDPR screenshot placeholders and their downloader are removed.
The 900×506 theme thumbnail is derived from `01.png` and included in the repository.

The installed, user-owned staged wallpaper directory was refreshed directly,
with `01.png` selected through native background IPC. Installed checksums and the
native picker cache confirm all 13 thumbnails in order. This wallpaper-only update
preserved the active desktop/plugin selection and stock-lock safe mode.

README uses the supplied artwork and native Omarchy-specific feature/control
sections. Fresh curated UI/auth media is now generated; see the public showcase
checkpoint above. Original appearance/authentication acceptance remains recorded
separately from the new non-authenticating showcase renders.

After the artwork/default-path and lifecycle-fixture updates, all 26 tests, Bash
syntax, pinned-lock/palette checks, lock-plugin validation, live integration and
`git diff --check` pass. The new wallpaper set is ready for fresh showcase capture.

| Area | Accepted/proven | Remaining |
| --- | --- | --- |
| Desktop/menu | Native caller select/input return/cancel/detail delivery, back and real Apps launch pass. Wrap/rapid-empty search exercised in actual QML. Extra Qt scales 1.5/2 and reduced motion render/focus checks pass. Earlier mouse/heading/fade acceptance retained. | Physical trackpad not attached; actual extra-output/compositor-scale acceptance not established by Qt scaling tests. |
| Notifications/OSD | Actual notification QML delivery, dismissal/history replay, DND and default actions pass in private sessions at normal/reduced motion and Qt scale 1.5. Repeated OSD transitions and auto-hide pass on the live desktop. | Broader hardware-specific visual acceptance; private-session tests do not replace every native caller sample. |
| Sudo/Polkit | Real auth/retry/cancel passed. Sudo capture-failure fallback and native off-theme terminal routing accepted live. Correct masks/caret/placeholder presentation accepted. | Fingerprint unavailable; installed PAM did not request a visible response. Further auth-scale/special-response acceptance needs a supporting setup. |
| Session lock | Manual/repeated/deferred unlock, live controlled-screensaver-class wallpaper fallback and native idle/DPMS blank/wake passed, including first-key feedback. Capture guards pass. Stock restored. | Suspend refocus click still reproduced in both stock/custom. Native screensaver animation startup and extra-output/scale cases remain unaccepted. |
| Runtime policy/lifecycle | Normal/missing-link native lifecycle and public CLI toggle/theme round-trips pass with unrelated settings and safe mode preserved. Sixteen isolated lifecycle/CLI tests cover fresh base-only defaults, migration, persistence, read-only inspection, interruption, conflicts and concurrency. | New-machine/second-user end-to-end installation and broader race/hardware cases remain release qualifications. |
| Retired work | Installed-system cleanup and active-checkout cleanup complete. Experimental implementation, removal helper and tests are in the external archive. | None; boot/login is outside product scope. |

### Retirement completed

Owned boot worker/watcher, Plymouth assets, SDDM override/themes and shared root
state are removed; stock Plymouth remains `omarchy`. Native login/autologin/PAM
were preserved. After the user's stock reboot, residual cached SDDM assets were
removed and absence verified. The removal-only helper and tests are now archived,
obsolete system guards removed, and stale bytecode caches cleared. Active hooks,
lock policy, palette and three auth previews have no dependency on archived work.
Detailed historical findings and migration code live in the external archive.

Retain safe mode only for current session-lock acceptance. Use the public
`cyberpunk` component controls; `scripts/lock-screen trial|restore` remains internal
supervised tooling. No three-screen matrix or boot/greeter lifecycle remains.
Do not use compositor Lua probes for live review:
a previous probe likely triggered Hyprland watchdog recovery.

## Remaining ordered product work

### Verification of the reduced scope

The retained suite has **32 passing tests**: sudo transport/editing/presentation,
shared lock/Polkit input and rhythm, palette propagation, wheel accumulation,
lock-only policy, screensaver capture refusal, failed-capture cleanup and private
capture publication, plus sixteen lifecycle/CLI/preference transaction tests.
Retirement-only tests are preserved with their archived helper.
All five plugin manifests, Bash syntax, palette and pinned-lock checks,
`scripts/verify --check`, three-screen preview motion contracts, and
`git diff --check` pass. Current manual/repeated/deferred lock acceptance and the
normal and partial native uninstall/reinstall cycles passed. Extra native-QML
regressions are recorded below separately from isolated CLI simulator coverage.

### 1. Finish input geometry polish

- [x] Center `ENTER PASSWORD` in the **whole bordered field** on lock/sudo/Polkit.
  Symmetric 56 px margins (plus symmetric fingerprint reserve on lock) center the
  placeholder while reserving space for `>`. Native input, masks/caret/hit-testing
   retain their accepted geometry. User accepted current lock, sudo and Polkit
   centering in real authentication dialogs.
- [ ] Keep the 4 px left/1 px other border recipe and translucent fills consistent.
  Check physical-pixel alignment at supported scales.
- [ ] Verify Home/End, arrows, insertion/deletion, selection replacement/drag,
  overflow and empty-field single red caret. Polkit visible responses retain native
  text cursor geometry; masked native cursor delegates remain empty.
- [x] Refresh and validate three retained offline previews after centering. Do not
  restore boot/greeter artifacts to `preview/`.

### 2. Complete desktop and auth regressions

- [x] Native menu select/input return/cancel and stable label/detail delivery,
  submenu back, real Apps launch, repeated OSD and auto-hide. The Apps probe was a
  temporary desktop entry launching a self-expiring, separately identified terminal;
  its entry/window were removed afterward. No arbitrary real application was closed.
- [x] Menu wrap and repeated empty/nonmatching search exercised in the actual QML
  instance; root/System/Apps render and focus at Qt scales 1.5/2 and reduced motion.
  These are logical Qt-scaling checks, not physical monitor-scale acceptance.
  No physical trackpad is attached in the current Hyprland device list; angle/pixel
  accumulation remains covered by the retained test. Actual wheel/hover acceptance
  was already recorded in the earlier supervised root/Keybindings review.
- [x] Actual notification QML: delivery, wrapped message, dismissal, history replay,
  DND suppression and default action receipt in private D-Bus/HOME sessions.
  Normal/reduced-motion/1.5 Qt-scale runs all passed. Production DND/history were
  never cleared or substituted. Private portal/accessibility activation left a stale
  AT-SPI socket; its native user service was restarted and connectivity verified.
- [x] Live OSD repeated volume → volume → mute → brightness → media/action messages
  and timer auto-hide. Payloads are IPC samples, not real volume/power changes.
  A subsequent microphone payload also opened and auto-hid normally.
- [x] Sudo native cancellation (exit 1, no accepted credential), wrong/correct auth,
  forced-grim-failure readable fallback with masks/caret/cancel, and off-theme native
  terminal routing (exit 0). Off-theme branch used an isolated HOME/theme marker in
  a real terminal, preserving the desktop theme. Retained PTY tests cover scripted
  and explicit noninteractive/stdin routing and a relocated checkout with spaces.
- [x] Polkit wrong-password → correct-password retry (exit 0) and Escape cancellation
  (exit 126) accepted by the user through the native agent. Fingerprint is not
  configured, and these installed PAM requests do not expose visible responses;
  those flows are not falsely marked live-passed. Capture-failure/off-theme visual
  variants beyond earlier native restoration evidence remain additional cases.
- [x] Reduced-motion and hide/accept/cancel timer contracts covered by retained auth
  tests and actual menu/notification reduced-motion instances.
  Sudo/Polkit shuffle 0.85/1.10/1.40-second sequences with 350–800 ms pauses;
  lock's effect remains brief and settling.

### 3. Current session-lock acceptance

- [x] While Cyberpunk is selected and stock lock is unlocked/PAM-ready:

  ```sh
  scripts/build-lock --check
  scripts/lock-screen trial
  ```

- [x] Supervised manual lock: user confirmed first-key input, correct/wrong
  password/retry, centered placeholder, mask/caret editing and backdrop/effect.
  Lock activation and stock restoration both verified PAM-ready/unlocked state.
- [x] Live fallback guard: a controlled `org.omarchy.screensaver` terminal existed
  when lock was requested through native lock IPC. The lock became secure; neither
  final capture nor partial file was published. User accepted wallpaper fallback,
  first-key masks and normal unlock. This does not validate the native screensaver
  animation launcher, whose cursor code was deliberately not rerun.
- [x] Native idle lock with temporary 5-second timeout; actual DPMS off/on verified
  with monitor status while the secure lock stayed active. User confirmed first-key
  feedback without clicking and normal unlock. The worker exceeded its 120-second
  wait while the user reviewed/unlocked: it kept the secure surface intact and
  disabled further idle cycles. After confirmed unlock, explicit deferred cleanup
  restored original idle 150/300 settings, stay-awake state and stock lock. Result
  records this timeout/cleanup rather than claiming the worker exited successfully.
- [ ] Suspend no-click focus, native screensaver animation startup and actual
  multi-output/auth-scale cases. Automated capture tests cover refusal, failed
  cleanup and mode 600 output; repeated locking was already accepted. Suspend
  authentication remains functional after clicking, with the shared issue below.
- [x] Secure deferred-restoration check: while the custom lock was secure, remove
  its trial authorization and run `verify --repair`. The transition unit queued;
  custom plugin and secure surface remained active. After user unlock, stock lock
  restored automatically; unit exited with success. General theme-switch/race
  scenarios remain part of lifecycle tests; never destroy active `WlSessionLock`.
- [x] After unlocking, `scripts/lock-screen restore`; stock service/PAM verified,
  no trial marker remains and global lock safe mode stays on.
- [x] Record current revision and actual live results separately from offline
  previews. Keep safe mode until the remaining issues are resolved or explicitly
  accepted by the user; stock-reproduced issues are not automatically passed.

**Shared wake-focus limitation:** two custom suspend/resume trials required a
click before masks/input feedback appeared. A stock-lock suspend/resume reproduced
the same symptom on the same setup. Only one active screen was reported after
wake, so there is no evidence to blame the disabled dummy for this lock case.
Whether pre-click keystrokes were retained was not established. A speculative
native-reactivation focus hook passed isolated tests but failed the real trial;
it was removed rather than shipped. Native focus/PAM/secure-surface behavior is
retained. Investigate this as a shared lock/compositor wake issue independently;
authentication still succeeded after clicking. No compositor Lua probes were used.

### 4. Lifecycle and release gates

- [ ] Theme picker: Cyberpunk → stock → Cyberpunk with lock enabled/disabled.
  Choices persist; native desktop services restore without overwriting external edits.
- [ ] Interrupted hooks/concurrent switches: deferred lock transition, ownership
  collisions and safe recovery. No system-wide boot/display-manager activity.
- [x] Full active-theme uninstall → verify removed → repeated uninstall → reinstall
  completed as a detached one-shot user service. Restored saved lock preference
  and background; current integration/PAM checks pass. Compared unrelated shell
  configuration (excluding managed clone/source plugin policy and normalizing the
  menu identity), Bash contents excluding the exact managed stanza, and Bash mode;
  all matched. Source/private artwork retained and safe mode stayed on.
- [x] Native missing-link recovery cycle: deliberately removed owned menu/OSD links,
  then uninstall → removed check → second uninstall → reinstall. Unrelated shell,
  Bash contents/mode, existing baseline and safe mode all preserved. Detached result:
  `/tmp/opencode/cyberpunk-recovery-result.json`, all comparisons true.
- [x] Ten isolated tests execute the real lifecycle scripts against simulated native
  APIs: clean first install/reinstall, failures before/after theme selection,
  missing theme/clone links with stale references, interrupted removal, foreign-link
  and edited-marker refusal, active-secure-lock refusal, operation serialization,
  incomplete-baseline refusal, concurrent user theme selection preserved during
  rollback and protection for a different newly active clone. Fixture checkouts
  contain spaces and a colon, avoiding delimiter-based path parsing. Simulation
  does not claim every real shell race/crash window is covered.
- [x] Portable baseline/ownership implementation: first install atomically creates a
  private snapshot; existing complete baselines are retained, incomplete/untrusted
  baselines refused. Askpass resolves relative to the sourced checkout rather than
  a personal Projects path. Installation/removal share a separate operation lock;
  reconciliation can still run from native theme hooks without deadlocking.
- [ ] Validate the documented first install end-to-end in a pristine supported user
  session/machine. Isolated HOME testing uses simulated native APIs; live native
  reinstall testing uses this machine's existing baseline and supported release.
- [ ] Review diagnostics/legacy migration helpers and repository references before
  further cleanup. Keep production plugins, reproducible previews, meaningful tests,
  notices/licences and private data ignored.
- [x] Run relevant tests, palette/pinned-lock checks, all plugin validations,
  lifecycle acceptance and `git diff --check`. Earlier preview acceptance remains
  historical; new showcase captures must be regenerated with the supplied artwork.
- [ ] README reflects only verified desktop/auth behavior and exact supported
  environment; validate documented commands on a clean supported install.
- [ ] Clear `.state/safe-mode` only after current lock and lifecycle gates pass
  with user approval. Commit/push only when separately requested.

**Latest execution checkpoint:** 32 retained tests and native integration checks
pass. Portable baseline creation/relocated sudo and recoverable removal implemented.
Native partial lifecycle, desktop caller/Apps/OSD, supervised auth retry/cancel/sudo
fallback/off-theme, controlled lock fallback and native idle/DPMS acceptance recorded.
Extra actual-QML scale/motion/history/action checks passed in private sessions.
Stock lock active/PAM-ready, safe mode on, saved preference enabled and no trial.
Idle configuration/stay-awake restored. Boot/login remains retired.

Evidence under `/tmp/opencode/` is local/temporary: `cyberpunk-recovery-result.json`,
`cyberpunk-desktop-result.json`, `cyberpunk-auth-*.json`, `cyberpunk-lock-{fallback,idle}.json`,
`cyberpunk-notifications-{normal,reduced,scaled}.json`, `cyberpunk-menu-{scales,interactions}.json`.
The idle result retains `workerTimedOut` and successful post-unlock cleanup details.

**Release qualifications still open:** shared suspend refocus acceptance/resolution,
true new-user/machine install, physical multi-output/auth-scale/special-response
coverage and finer visual/input geometry cases. Qt scaling/simulation are not proof
of these hardware cases. No further suspend trials or speculative focus patches
without new evidence; safe-mode clearance still requires explicit user approval.
