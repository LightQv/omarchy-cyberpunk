# Omarchy compatibility

This branch targets the reviewed **Omarchy 4.5.0-3** package (upstream **v4.5.0**).
Copied plugins do not automatically receive upstream fixes after a system update.

## 4.5 qualification and transition

The baseline is from the stable x86_64 package, verified with the installed
Omarchy public key. The package's SHA-256 and upstream commit are recorded in
`scripts/omarchy-baseline.json`; its 70 tracked source files are checked before
an installer transaction changes live providers. **Live system qualification is
pending: this branch must initially ship as a prerelease, not a stable claim.**

The port retains Cyberpunk's command-wheel and authentication presentation while
incorporating the 4.5 menu's disabled rows, multi-selection, IME/filter handling,
translations and source-loading fixes. Notifications use the native 4.5 engine
and security helpers, with a presentation-only angular frame. The lock is built
from the complete new service, preserving wake-key repeat filtering, password
focus recovery, fingerprint pacing, suspend/resume handling and video posters.
Safe mode remains enabled until a separate secure lock/unlock acceptance.

The old notification history is retired by Omarchy's own migration. Back it up
before updating; do not copy its old JSON files over the 4.5 store.

Upgrade order for an existing 4.0.4-1 installation:

1. Back up home customizations as well as the system snapshot; Omarchy's root
   snapshots can exclude home. Preserve the existing lock safe-mode marker.
2. Select a bundled native theme through `omarchy theme set`. This keeps saved
   Cyberpunk choices but restores native providers before upgrading their host.
3. Run the official full stable Omarchy update, not a partial package upgrade.
4. Once Omarchy reports the supported package version, run `cyberpunk update`.
   During qualification, use the same installed release bootstrap with an explicit
   prerelease tag: `bash ~/.local/share/omarchy-cyberpunk/install.sh --version v0.2.0`.
   This downloads the GitHub asset and verifies both checksum and file manifest;
   it is not a checkout install or a direct edit of installed plugins.
5. Select Cyberpunk, run `cyberpunk check`, and test the saved component choices,
   palette, apps/search, notifications/actions/DND, OSD, Polkit, QR65 and shortcuts.
   Test login/reboot/suspend separately. Only then promote the release to stable.

Checkout verification against an extracted signed package (no live installation):

```sh
python -B scripts/rebase-omarchy-4.5.py --check --old-root /path/to/4.0.4/usr/share/omarchy --new-root /path/to/4.5/usr/share/omarchy
python -B scripts/build-lock --check --omarchy-root /path/to/4.5/usr/share/omarchy
OMARCHY_TEST_ROOT=/path/to/4.5/usr/share/omarchy ./dev test
```

The component test isolates HOME, configuration, state, runtime and both D-Bus
buses. It uses the current Wayland connection only for Quickshell's backend;
it never instantiates a lock service, submits a password or changes live providers.

## Read-only checks

```sh
cyberpunk compatibility                   # Installed version and upstream source hashes
cyberpunk compatibility --upstream        # Also query the latest stable GitHub release
cyberpunk compatibility --upstream --json # Machine-readable report
cyberpunk check                           # Compatibility plus integration/preferences
```

These commands are available in Cyberpunk **v0.1.5 and later**. From a checkout,
run `python -B scripts/compatibility.py [--upstream] [--json]`.
The default audit is offline, reads `/usr/share/omarchy`, and checks every tracked
source even when a component is disabled or the native lock is selected.
It changes no settings or providers. Exit codes: `0` matches the reviewed baseline,
`1` needs review, `2` means the check could not finish (including network errors).
A successful source audit is not a substitute for live acceptance testing.

`scripts/omarchy-baseline.json` records the package version, upstream repository,
tag and commit, original source paths, SHA-256 hashes, and copied-file destinations.
The hashes were taken from the installed stable package, not our modified clones.
It also tracks the shell entry point and all shared Commons/Ui files conservatively;
a changed shared file calls for review even if its API remains compatible. Other
dependencies, such as Qt, Quickshell, Hyprland, CLI behavior and plugin discovery,
need regression and live testing; they are not certified by this source inventory.
Packaging, installer validation and lock generation use this same baseline.

## Stable-release monitoring

`.github/workflows/omarchy-compatibility.yml` checks upstream daily at 08:17 UTC
(GitHub may delay scheduled runs), and supports manual dispatch. With Actions
and Issues enabled on the default branch, it opens one review issue
per newer stable release. Existing open **or closed** review issues prevent repeats.
Development commits and prereleases do not trigger review issues.

The monitor only needs repository-read and issue-write permissions. It never
updates the support declaration or desktop automatically. GitHub can disable
scheduled workflows after 60 days without repository activity; check Actions
periodically and re-enable the schedule if necessary.

To inspect the monitor locally without creating an issue:

```sh
python -B scripts/watch-omarchy-release.py
```

This uses the authenticated `gh` CLI. API/network failures fail the workflow rather
than reporting that Omarchy is current.

## Accepting a new release

1. Fetch the stable release in a separate supported user/session, VM or machine.
   Keep packaged `/usr/share/omarchy` read-only. Save the previous baseline and use
   the recorded commit to compare against the new upstream tag.
2. Review all original paths in `copies`, preserving Cyberpunk presentation while
   incorporating upstream fixes. Inspect shared QML imports, shell/plugin discovery,
   IPC payloads, theme commands, configuration and migrations. Review Polkit/PAM and
   secure-lock changes explicitly; do not bypass a changed lock hash to make it load.
3. Run `./dev test`. Build with `./dev build vX.Y.Z` and inspect its runtime-only
   file manifest, version contract and checksums. Installer support must match the
   reviewed package version, including Arch's package revision.
4. In the isolated live session, verify first install, update with saved preferences,
   recovery/removal, provider switching, menu/app search, notifications/DND/actions,
   OSD, Polkit failure/retry/success and lock/unlock. Keep active secure surfaces intact;
   lock changes remain deferred until unlocked and PAM-ready. Record hardware,
   fingerprint and suspend/resume qualifications separately.
5. After review, edit `scripts/omarchy-baseline.json`: version, tag, commit and source
   hashes. Add newly introduced dependencies, remove retired paths, update modified
   clones and regenerate the lock with `python -B scripts/build-lock --write`.
   There is intentionally no automatic "accept current hashes" command.
6. Run the audit/tests again, update README requirements and provenance, publish a
   new versioned Cyberpunk runtime, and close the corresponding review issue with
   verification evidence. Do not advertise support based on unit tests alone.

## Existing installations after an Omarchy update

The managed installer rejects a package version that differs from its supported
baseline. The new read-only `cyberpunk check` detects changed source files as well.
It does not automatically replace or unload running providers, and `repair` retains
its recovery behavior. Existing v0.1.4 installations can run `cyberpunk update`
to receive the general audit in v0.1.5; their existing lock-pin safeguards remain.

Since **v0.1.6**, the installer explicitly commits the restored theme's staged
palette to the running shell after installation, update, same-version reinstall
and recovery. It requires the shell's `ok` acknowledgement; a failed commit enters
the normal rollback/recovery path. This corrects cases where the selected theme
and files were Cyberpunk but the bar, OSD and theme-following plugins retained a
previous native theme's colors. The saved default/inverted scheme is preserved.
