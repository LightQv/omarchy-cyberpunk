#!/usr/bin/env python3
"""Install release files into Omarchy's native layout with journaled rollback."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
DEST = Path(os.environ.get("XDG_DATA_HOME", str(HOME / ".local/share"))) / "omarchy-cyberpunk"
STATE = Path(os.environ.get("XDG_STATE_HOME", str(HOME / ".local/state"))) / "omarchy-cyberpunk"
TRANSACTION = STATE / "release-transaction"
CURRENT = HOME / ".local/state/omarchy/current"
LAYOUT = {"theme": HOME / ".config/omarchy/themes/cyberpunk"}
LAYOUT.update({kind + "-plugin": HOME / ".config/omarchy/plugins" / ("lightqv.cyberpunk-" + kind)
               for kind in ("menu", "polkit", "notifications", "osd", "lock")})
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def trusted(path, directory=False):
    info = path.lstat()
    if info.st_uid != os.getuid() or info.st_mode & 0o022 or not (
            stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError(f"Untrusted installation path: {path}")


def parents(path):
    for parent in reversed(path.parents):
        if parent == HOME or HOME in parent.parents:
            if parent.exists() or parent.is_symlink():
                trusted(parent, True)
    path.parent.mkdir(parents=True, exist_ok=True)


def record(path):
    if path.is_symlink():
        return {"link": os.readlink(path)}
    trusted(path)
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mode": stat.S_IMODE(path.stat().st_mode)}


def inventory(directory, support=False):
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if support and (relative.parts[0] in LAYOUT or relative.parts[0] == "managed.json"):
            continue
        if path.is_symlink() or path.is_file():
            result[str(relative)] = record(path)
        elif not path.is_dir():
            raise ValueError(f"Unexpected installed file: {path}")
    return result


def write_json(path, data):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        json.dump(data, output, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.chmod(0o600)
    temporary.replace(path)


def metadata(root):
    trusted(root, True)
    trusted(root / "managed.json")
    return json.loads((root / "managed.json").read_text())


def owned(root, path):
    data = metadata(root)
    label = next((name for name, target in LAYOUT.items() if target == path), None)
    if label is None:
        raise ValueError(f"Not a managed project directory: {path}")
    trusted(path, True)
    if inventory(path) != data["directories"][label]:
        raise ValueError(f"Installed files were edited or added: {path}; preserve/revert them before updating or removing")


def check_support(root):
    data = metadata(root)
    if inventory(root, support=True) != data["support"]:
        raise ValueError(f"Support files were edited or added: {root}")
    for label, target in LAYOUT.items():
        link = root / label
        if not link.is_symlink() or os.readlink(link) != str(target):
            raise ValueError(f"Managed support link changed: {link}")


def validate_payload(payload):
    trusted(payload, True)
    trusted(payload / "release.json")
    release = json.loads((payload / "release.json").read_text())
    actual = inventory(payload)
    actual.pop("release.json", None)
    if actual != release["files"] or any("link" in entry for entry in actual.values()):
        raise ValueError("Release contents differ from the packaged manifest")
    if not release["version"].startswith("v") or release["omarchy"] != "4.0.4-1":
        raise ValueError("Unsupported release contract")
    return release


def run_script(root, script, staging=False):
    environment = dict(ENV, CYBERPUNK_LIFECYCLE_FD="7")
    if staging:
        environment["CYBERPUNK_RELEASE_STAGING"] = "1"
    else:
        environment.pop("CYBERPUNK_RELEASE_STAGING", None)
    subprocess.run([str(root / "scripts" / script)], env=environment, pass_fds=(7,), check=True)


def native(*args):
    subprocess.run(["omarchy", *args], env=ENV, check=True)


def lock_ready():
    result = subprocess.check_output(["omarchy-shell", "lock", "status"], env=ENV, text=True)
    state = json.loads(result)
    if any(state.get(key, True) for key in ("locked", "requested", "sessionLocked", "secure")) or not state.get("passwordPam"):
        raise ValueError("Install/update/remove only while unlocked and PAM-ready")
    locked = subprocess.run(["omarchy-hyprland-session-locked"], env=ENV).returncode
    if locked != 1:
        raise ValueError("Session lock state is not safely unlocked")


def materialize(root, target):
    shutil.copytree(root, target, ignore=shutil.ignore_patterns("managed.json", ".state", "__pycache__"))


def populate(payload):
    parents(DEST)
    shutil.copytree(payload, DEST)
    run_script(DEST, "install-dev", staging=True)
    data = {"directories": {label: inventory(DEST / label) for label in LAYOUT},
            "support": inventory(DEST, support=True)}
    # Record ownership before converting any native link, so partial conversion
    # can still be removed safely by the existing interrupted-uninstall path.
    write_json(DEST / "managed.json", data)
    for label, target in LAYOUT.items():
        if not target.is_symlink() or os.readlink(target) != str(DEST / label):
            raise ValueError(f"Staged project link changed: {target}")
        target.unlink()
        (DEST / label).rename(target)
        (DEST / label).symlink_to(target, target_is_directory=True)


def restore_view(journal, fresh=False):
    selected = "cyberpunk" if fresh else journal["theme"]
    native("theme", "set", selected)
    wallpaper = journal.get("wallpaper")
    if selected == "cyberpunk" and journal.get("bundledWallpaper"):
        wallpaper = str(LAYOUT["theme"] / "backgrounds" / journal["bundledWallpaper"])
    if fresh:
        wallpaper = str(LAYOUT["theme"] / "backgrounds/01.png")
    if wallpaper and Path(wallpaper).is_file():
        native("theme", "bg", "set", wallpaper)
    run_script(DEST, "verify")


def recover():
    trusted(TRANSACTION, True)
    trusted(TRANSACTION / "journal.json")
    journal = json.loads((TRANSACTION / "journal.json").read_text())
    print("Recovering the interrupted release transaction…", flush=True)
    if DEST.exists():
        # Refuse removal of modified support files when a completed manifest exists.
        if (DEST / "managed.json").exists():
            if inventory(DEST, support=True) != metadata(DEST)["support"]:
                raise ValueError("Support files changed during recovery; transaction retained")
        run_script(DEST, "uninstall-dev")
        shutil.rmtree(DEST)
    if journal["oldKind"] == "managed":
        populate(TRANSACTION / "previous")
        restore_view(journal)
    elif journal["oldKind"] == "legacy":
        old = Path(journal["oldRoot"])
        run_script(old, "uninstall-dev")
        run_script(old, "install-dev")
        native("theme", "set", journal["theme"])
        if journal.get("wallpaper") and Path(journal["wallpaper"]).is_file():
            native("theme", "bg", "set", journal["wallpaper"])
    else:
        native("theme", "set", journal["theme"])
        if journal.get("wallpaper") and Path(journal["wallpaper"]).is_file():
            native("theme", "bg", "set", journal["wallpaper"])
    shutil.rmtree(TRANSACTION)


def install(payload):
    release = validate_payload(payload)
    version = subprocess.check_output(["omarchy", "version"], env=ENV, text=True).strip()
    if version != release["omarchy"]:
        raise ValueError(f"This release supports Omarchy {release['omarchy']}; found {version}")
    subprocess.run(["python", "-c", "import PySide6.QtQuickWidgets"], env=ENV, check=True)
    lock_ready()
    if TRANSACTION.exists() or TRANSACTION.is_symlink():
        trusted(TRANSACTION, True)
        if (TRANSACTION / "journal.json").exists():
            recover()
        else:
            # Snapshot preparation precedes all live mutation. A kill during the
            # snapshot can leave scratch files but no committed journal.
            shutil.rmtree(TRANSACTION)
    old = None
    kind = "none"
    if DEST.exists() or DEST.is_symlink():
        check_support(DEST)
        for target in LAYOUT.values():
            owned(DEST, target)
        old, kind = DEST, "managed"
    elif LAYOUT["theme"].is_symlink():
        old = LAYOUT["theme"].resolve().parent
        if not (old / "scripts/common.sh").is_file() or LAYOUT["theme"].resolve() != old / "theme":
            raise ValueError("Existing Cyberpunk theme is not a supported project checkout")
        subprocess.run([str(old / "scripts/verify"), "--check"], env=ENV, check=True)
        old, kind = old, "legacy"
    elif LAYOUT["theme"].exists():
        raise ValueError("Cyberpunk theme path is occupied by an unmanaged directory")
    if old and (old / "release.json").exists() and json.loads((old / "release.json").read_text())["version"] == release["version"]:
        if json.loads((old / "release.json").read_text()) != release:
            raise ValueError("A published version must not change its files; use a new release version")
        run_script(old, "verify")
        print(f"Cyberpunk {release['version']} is already installed.")
        return
    if kind == "legacy":
        if (old / ".state/lock-trial").exists():
            raise ValueError("Restore the isolated lock trial before migration")
        subprocess.run(["python", "-B", str(old / "scripts/preferences.py"), "init"], env=ENV, check=True)
        for name in ("safe-mode", "previous-theme"):
            source = old / ".state" / name
            if source.exists():
                trusted(source)
                shutil.copyfile(source, STATE / name)
                (STATE / name).chmod(0o600)
    # Preflight occupied plugin/hook/CLI paths before removing an old installation.
    if kind == "none":
        extras = [HOME / ".local/bin/cyberpunk"]
        extras += [HOME / ".config/omarchy/hooks" / name / "lightqv-cyberpunk-menu"
                   for name in ("theme-set.d", "post-boot.d")]
        for target in [*LAYOUT.values(), *extras]:
            parents(target)
            if target.exists() or target.is_symlink():
                raise ValueError(f"Installation path is occupied: {target}")
    journal = {"oldKind": kind, "oldRoot": str(old) if old else None,
               "theme": (CURRENT / "theme.name").read_text().strip(), "wallpaper": None}
    background = CURRENT / "background"
    if background.exists():
        original = background.resolve()
        journal["wallpaper"] = str(original)
        candidates = [CURRENT / "theme/backgrounds", LAYOUT["theme"] / "backgrounds"]
        if old:
            candidates.append(old / "theme/backgrounds")
        if any(original.parent == path.resolve() for path in candidates):
            journal["bundledWallpaper"] = original.name
    TRANSACTION.mkdir(mode=0o700)
    try:
        if kind == "managed":
            materialize(old, TRANSACTION / "previous")
        write_json(TRANSACTION / "journal.json", journal)
    except BaseException:
        shutil.rmtree(TRANSACTION)
        raise
    try:
        if old:
            run_script(old, "uninstall-dev")
            if kind == "managed":
                shutil.rmtree(DEST)
        populate(payload)
        restore_view(journal, fresh=kind == "none")
    except BaseException:
        # The inner install trap may have unlocked the inherited operation lock.
        fcntl.flock(7, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            recover()
        except Exception as error:
            print(f"Recovery incomplete: {error}. Rerun the release installer while unlocked; journal retained at {TRANSACTION}", file=sys.stderr)
        raise
    shutil.rmtree(TRANSACTION)
    print(f"Cyberpunk {release['version']} installed. Run cyberpunk status.", flush=True)


def uninstall():
    lock_ready()
    if TRANSACTION.exists():
        raise ValueError("Recover the interrupted transaction with the release installer first")
    check_support(ROOT)
    # Existing uninstall preflights all native directory ownership before mutation.
    run_script(ROOT, "uninstall-dev")
    shutil.rmtree(ROOT)
    print("Managed runtime files removed; preferences and private recovery baseline retained.")


def main():
    action = sys.argv[1]
    if action in ("owned", "remove-path"):
        path = Path(sys.argv[2])
        owned(ROOT, path)
        if action == "remove-path":
            shutil.rmtree(path)
        return
    if os.getuid() == 0:
        raise ValueError("Run the release installer as your desktop user, without sudo")
    parents(STATE)
    STATE.mkdir(exist_ok=True, mode=0o700)
    trusted(STATE, True)
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    descriptor = os.open(runtime / "lightqv-cyberpunk-lifecycle.lock.operation", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    if os.fstat(descriptor).st_uid != os.getuid():
        raise ValueError("Untrusted lifecycle lock")
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.dup2(descriptor, 7)
    if action == "install":
        install(Path(sys.argv[2]).resolve())
    elif action == "uninstall":
        uninstall()
    else:
        raise ValueError("Unknown release action")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Cyberpunk: {error}", file=sys.stderr)
        sys.exit(1)
