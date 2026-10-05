#!/usr/bin/env python3
"""Open one compatibility-review issue per newer stable Omarchy release."""

import argparse
import json
import os
import re
import subprocess

from compatibility import load_baseline, release_version


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True, timeout=60).strip()


def review_body(baseline, release):
    tag = release["tag_name"]
    repository = baseline["repository"]
    return f"""A newer stable Omarchy release needs compatibility review.

- Reviewed package: **{baseline['packageVersion']}** ({baseline['tag']})
- New release: **{tag}** — https://github.com/{repository}/releases/tag/{tag}
- Baseline commit: `{baseline['commit']}`
- Upstream diff: https://github.com/{repository}/compare/{baseline['commit']}...{tag}
- Source inventory: `scripts/omarchy-baseline.json`
- Review procedure: `docs/COMPATIBILITY.md`

### Acceptance
- [ ] Compare copied menu/app discovery, notification, OSD, Polkit and lock sources.
- [ ] Review shared Commons/Ui, shell/plugin APIs, CLI commands and migrations.
- [ ] Incorporate relevant upstream fixes while preserving Cyberpunk styling.
- [ ] Run isolated regression tests and build/inspect the runtime archive.
- [ ] Verify live install/update/removal and native/custom provider switching in a separate supported session.
- [ ] Verify menu/search, notifications/DND/actions, OSD, Polkit failure/retry/success and lock/unlock.
- [ ] Document any outstanding hardware/suspend qualifications.
- [ ] Update baseline hashes/version/tag/commit and publish a verified Cyberpunk release.

Detection does not certify compatibility or change installed providers.
"""


def monitor(baseline, release, repository, create=False):
    tag = release["tag_name"]
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Expected a stable release")
    if release_version(tag) <= release_version(baseline["tag"]):
        return "Reviewed baseline is current; no issue needed."
    title = f"Omarchy {tag} compatibility review"
    if not create:
        return f"Would open: {title}\n\n{review_body(baseline, release)}"
    # Include closed issues: a completed or deliberately closed review must not
    # reopen every day. The workflow serializes runs to avoid duplicate creation.
    issues = json.loads(gh("issue", "list", "--repo", repository, "--state", "all",
                           "--search", f'"{title}" in:title', "--json", "title,url", "--limit", "100"))
    existing = next((issue for issue in issues if issue["title"] == title), None)
    if existing:
        return f"Review already exists: {existing['url']}"
    return gh("issue", "create", "--repo", repository, "--title", title,
              "--body", review_body(baseline, release))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-issue", action="store_true", help="Create an issue; default is read-only")
    parser.add_argument("--repo", default=os.environ.get("GH_REPO", "LightQv/omarchy-cyberpunk"))
    args = parser.parse_args()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        parser.error("Use an owner/repository name")
    baseline = load_baseline()
    release = json.loads(gh("api", f"repos/{baseline['repository']}/releases/latest"))
    print(monitor(baseline, release, args.repo, args.create_issue))


if __name__ == "__main__":
    main()
