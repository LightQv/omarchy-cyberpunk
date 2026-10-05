#!/usr/bin/env python3
"""Audit installed Omarchy sources against the reviewed baseline without changes."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

BASELINE = Path(__file__).with_name("omarchy-baseline.json")


def load_baseline(path=BASELINE):
    """Read and validate the source inventory shared by audits and release monitoring."""
    data = json.loads(path.read_text())
    if data.get("schemaVersion") != 1 or not data.get("files"):
        raise ValueError("Unsupported or empty Omarchy baseline")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", data["repository"]):
        raise ValueError("Invalid upstream repository")
    release_version(data["tag"])
    if not re.fullmatch(r"[0-9a-f]{40}", data["commit"]):
        raise ValueError("Invalid baseline commit")
    for name, digest in data["files"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid baseline entry: {name}")
    if not set(data["copies"]).issubset(data["files"]):
        raise ValueError("Copied sources must be included in the baseline")
    return data


def release_version(tag):
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        raise ValueError(f"Unexpected stable release tag: {tag}")
    return tuple(map(int, match.groups()))


def latest_release(baseline):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{baseline['repository']}/releases/latest",
        headers={"User-Agent": "omarchy-cyberpunk-compatibility", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    release_version(release["tag_name"])
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Upstream returned a non-stable release")
    return release


def audit(baseline, root, version):
    """Report mismatches for every component, independent of enabled preferences."""
    changes = []
    for name, expected in sorted(baseline["files"].items()):
        try:
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
            if actual != expected:
                changes.append({"path": name, "status": "changed", "expected": expected, "actual": actual})
        except OSError as exc:
            changes.append({"path": name, "status": "unavailable", "error": str(exc)})
    return {"supportedVersion": baseline["packageVersion"], "installedVersion": version,
            "compatible": version == baseline["packageVersion"] and not changes,
            "checkedFiles": len(baseline["files"]), "changes": changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--upstream", action="store_true", help="Also check GitHub's latest stable release (network required)")
    parser.add_argument("--omarchy-root", type=Path, default=Path("/usr/share/omarchy"), help="Source tree to audit")
    args = parser.parse_args()
    try:
        baseline = load_baseline()
        version = subprocess.check_output(["omarchy", "version"], text=True, timeout=10).strip()
        report = audit(baseline, args.omarchy_root, version)
        if args.upstream:
            release = latest_release(baseline)
            report["latestStable"] = release["tag_name"]
            report["reviewRequired"] = release_version(release["tag_name"]) > release_version(baseline["tag"])
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Omarchy: installed {version}; reviewed {baseline['packageVersion']}")
            print(f"Upstream source audit: {report['checkedFiles']} files; {len(report['changes'])} changed/unavailable")
            for change in report["changes"]:
                print(f"  {change['status']}: {change['path']}")
            if args.upstream:
                print(f"Latest stable: {report['latestStable']}; new release review required: {report['reviewRequired']}")
            print("Reviewed compatibility baseline matches." if report["compatible"] else "Compatibility review required; see docs/COMPATIBILITY.md.")
        return 0 if report["compatible"] and not report.get("reviewRequired") else 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        if args.json:
            print(json.dumps({"compatible": False, "error": str(exc)}))
        else:
            print(f"Compatibility audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
