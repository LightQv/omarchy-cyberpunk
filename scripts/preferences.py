#!/usr/bin/python
"""Persist component choices independently of the selected theme and checkout."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

COMPONENTS = ("menu", "notifications", "osd", "sudo", "polkit", "lock")
PROJECT = Path(__file__).resolve().parent.parent
DIRECTORY = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "omarchy-cyberpunk"
PATH = DIRECTORY / "preferences.json"
STATE = DIRECTORY if (PROJECT / "release.json").is_file() else PROJECT / ".state"


def trusted(path, directory=False):
    info = path.lstat()
    valid_type = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not valid_type or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ValueError(f"untrusted preferences path: {path}")


def legacy_defaults():
    """Migrate an existing installation, but default fresh installations to native."""
    values = dict.fromkeys(COMPONENTS, False)
    theme_link = Path.home() / ".config/omarchy/themes/cyberpunk"
    if not theme_link.is_symlink() or theme_link.readlink() != PROJECT / "theme":
        return values
    values.update(dict.fromkeys(COMPONENTS, True))
    legacy = PROJECT / ".state/lock-preference"
    if legacy.exists() or legacy.is_symlink():
        trusted(legacy)
        value = legacy.read_text().strip()
        if value not in ("enabled", "disabled"):
            raise ValueError("invalid legacy lock preference")
        values["lock"] = value == "enabled"
    theme = Path.home() / ".local/state/omarchy/current/theme.name"
    if theme.read_text().strip() == "cyberpunk":
        plugins = json.loads(subprocess.check_output(["omarchy", "plugin", "list", "--json"], text=True))
        enabled = {plugin["id"] for plugin in plugins if plugin["enabled"]}
        for component in ("menu", "notifications", "osd", "polkit"):
            values[component] = "lightqv.cyberpunk-" + component in enabled
    return values


def load():
    if DIRECTORY.exists() or DIRECTORY.is_symlink():
        trusted(DIRECTORY, directory=True)
    if not PATH.exists() and not PATH.is_symlink():
        return legacy_defaults()
    trusted(PATH)
    data = json.loads(PATH.read_text())
    if not isinstance(data, dict) or set(data) != {"version", "components"}:
        raise ValueError("invalid preferences document")
    values = data["components"]
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("unsupported preferences version")
    if not isinstance(values, dict) or set(values) != set(COMPONENTS) or any(type(value) is not bool for value in values.values()):
        raise ValueError("preferences require six boolean component choices")
    return values


def publish(values):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=DIRECTORY, prefix=".preferences.", delete=False) as output:
            temporary = Path(output.name)
            json.dump({"version": 1, "components": values}, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o600)
        temporary.replace(PATH)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def update(component=None, enabled=None):
    DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    trusted(DIRECTORY, directory=True)
    descriptor = os.open(DIRECTORY / "preferences.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+") as lock:
        trusted(DIRECTORY / "preferences.lock")
        fcntl.flock(lock, fcntl.LOCK_EX)
        values = load()
        if component is not None:
            for name in COMPONENTS if component == "all" else (component,):
                values[name] = enabled
        if component is not None or not PATH.exists():
            publish(values)
        return values


def status():
    values = load()
    theme_path = Path.home() / ".local/state/omarchy/current/theme.name"
    theme = theme_path.read_text().strip()
    plugins = json.loads(subprocess.check_output(["omarchy", "plugin", "list", "--json"], text=True))
    enabled = {plugin["id"] for plugin in plugins if plugin["enabled"]}
    safe = STATE / "safe-mode"
    trial = STATE / "lock-trial"
    safe_mode = safe.exists() or safe.is_symlink()
    trial_allowed = False
    if trial.exists() or trial.is_symlink():
        trusted(trial)
        trial_allowed = trial.read_text().strip() == "lock" and safe.is_file() and not safe.is_symlink()
    print(f"Theme: {theme}")
    print(f"Preferences: {PATH}" + (" (not initialized)" if not PATH.exists() else ""))
    print(f"{'COMPONENT':<16} {'PREFERENCE':<12} {'ACTUAL':<12} NOTE")
    for component in COMPONENTS:
        wanted = theme == "cyberpunk" and values[component]
        note = ""
        if component == "sudo":
            manager = PROJECT / "scripts/manage-bashrc.py"
            present = subprocess.run([str(manager), "check"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
            actual = "cyberpunk" if wanted and present else "native"
            note = "eligible interactive Bash sessions" if present else "Bash integration absent"
        else:
            clone = "lightqv.cyberpunk-" + component
            source = "omarchy." + component
            actual = "conflict" if clone in enabled and source in enabled else "cyberpunk" if clone in enabled else "native" if source in enabled else "unavailable"
            if component == "lock" and safe_mode and not trial_allowed:
                wanted = False
                note = "safe mode" if values[component] else "safe mode; preference disabled"
            elif component == "lock" and trial_allowed:
                note = "development trial"
            if actual != ("cyberpunk" if wanted else "native"):
                note = (note + "; " if note else "") + "pending or needs repair"
        if theme != "cyberpunk" and values[component]:
            note = (note + "; " if note else "") + "saved for Cyberpunk"
        print(f"{component:<16} {'enabled' if values[component] else 'disabled':<12} {actual:<12} {note}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("read", "init", "enabled", "set", "status"))
    parser.add_argument("component", nargs="?", choices=(*COMPONENTS, "all"))
    parser.add_argument("value", nargs="?", choices=("enabled", "disabled"))
    args = parser.parse_args()
    if args.action == "set":
        if args.component is None or args.value is None:
            parser.error("set requires component and enabled|disabled")
        update(args.component, args.value == "enabled")
    elif args.action == "init":
        update()
    elif args.action == "enabled":
        if args.component not in COMPONENTS:
            parser.error("enabled requires one component")
        return 0 if load()[args.component] else 1
    elif args.action == "status":
        status()
    else:
        print(json.dumps(load()))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Cyberpunk: {error}", file=sys.stderr)
        sys.exit(2)
