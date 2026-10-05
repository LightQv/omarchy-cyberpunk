# Omarchy compatibility

Cyberpunk supports the reviewed **Omarchy 4.0.4-1** package (upstream **v4.0.4**).
Copied plugins do not automatically receive upstream fixes after a system update.

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
