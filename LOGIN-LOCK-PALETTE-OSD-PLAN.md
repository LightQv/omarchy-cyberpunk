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

| Area | Accepted/proven | Remaining |
| --- | --- | --- |
| Desktop/menu | Native caller select/input return/cancel/detail delivery, back and real Apps launch pass. Wrap/rapid-empty search exercised in actual QML. Extra Qt scales 1.5/2 and reduced motion render/focus checks pass. Earlier mouse/heading/fade acceptance retained. | Physical trackpad not attached; actual extra-output/compositor-scale acceptance not established by Qt scaling tests. |
| Notifications/OSD | Actual notification QML delivery, dismissal/history replay, DND and default actions pass in private sessions at normal/reduced motion and Qt scale 1.5. Repeated OSD transitions and auto-hide pass on the live desktop. | Broader hardware-specific visual acceptance; private-session tests do not replace every native caller sample. |
| Sudo/Polkit | Real auth/retry/cancel passed. Sudo capture-failure fallback and native off-theme terminal routing accepted live. Correct masks/caret/placeholder presentation accepted. | Fingerprint unavailable; installed PAM did not request a visible response. Further auth-scale/special-response acceptance needs a supporting setup. |
| Session lock | Manual/repeated/deferred unlock, live controlled-screensaver-class wallpaper fallback and native idle/DPMS blank/wake passed, including first-key feedback. Capture guards pass. Stock restored. | Suspend refocus click still reproduced in both stock/custom. Native screensaver animation startup and extra-output/scale cases remain unaccepted. |
| Runtime policy/lifecycle | Normal and missing-link native uninstall/reinstall cycles pass with unrelated settings, modes, baseline and safe mode preserved. Ten isolated transaction tests cover interruption, conflicts, concurrency and clean first-install. | New-machine/second-user end-to-end installation and broader race/hardware cases remain release qualifications. |
| Retired work | Installed-system cleanup and active-checkout cleanup complete. Experimental implementation, removal helper and tests are in the external archive. | None; boot/login is outside product scope. |

### Retirement completed

Owned boot worker/watcher, Plymouth assets, SDDM override/themes and shared root
state are removed; stock Plymouth remains `omarchy`. Native login/autologin/PAM
were preserved. After the user's stock reboot, residual cached SDDM assets were
removed and absence verified. The removal-only helper and tests are now archived,
obsolete system guards removed, and stale bytecode caches cleared. Active hooks,
lock policy, palette and three auth previews have no dependency on archived work.
Detailed historical findings and migration code live in the external archive.

Retain safe mode only for current session-lock acceptance. Use
`scripts/lock-screen {status|enable|disable|trial|restore}`; no three-screen matrix
or boot/greeter lifecycle remains. Do not use compositor Lua probes for live review:
a previous probe likely triggered Hyprland watchdog recovery.

## Remaining ordered product work

### Verification of the reduced scope

The retained suite has **26 passing tests**: sudo transport/editing/presentation,
shared lock/Polkit input and rhythm, palette propagation, wheel accumulation,
lock-only policy, screensaver capture refusal, failed-capture cleanup and private
capture publication, plus ten lifecycle transaction/first-install tests.
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
  lifecycle acceptance and `git diff --check`. Earlier retained preview acceptance
  still applies; lifecycle-only changes do not alter their visual sources.
- [ ] README reflects only verified desktop/auth behavior and exact supported
  environment; validate documented commands on a clean supported install.
- [ ] Clear `.state/safe-mode` only after current lock and lifecycle gates pass
  with user approval. Commit/push only when separately requested.

**Latest execution checkpoint:** 26 retained tests and native integration checks
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
