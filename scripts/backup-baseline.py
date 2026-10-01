#!/usr/bin/python
"""Create a private first-install snapshot without replacing an earlier baseline."""

import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


def regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise ValueError(f"baseline requires an owned regular file: {path}")


def main() -> None:
    home = Path.home()
    destination = home / ".local/state/omarchy-cyberpunk-backup"
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError("baseline destination is not a regular directory")
        if destination.stat().st_uid != os.getuid():
            raise ValueError("baseline directory has another owner")
        for name in ("shell.json", "bashrc"):
            regular(destination / name)
        return
    sources = {"shell.json": home / ".config/omarchy/shell.json", "bashrc": home / ".bashrc"}
    for source in sources.values():
        regular(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".cyberpunk-baseline-", dir=destination.parent))
    try:
        modes = {}
        for name, source in sources.items():
            modes[name] = stat.S_IMODE(source.stat().st_mode)
            target = temporary / name
            with target.open("xb") as output:
                target.chmod(0o600)
                output.write(source.read_bytes())
                output.flush()
                os.fsync(output.fileno())
        (temporary / "modes.json").write_text(json.dumps(modes) + "\n")
        (temporary / "modes.json").chmod(0o600)
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Cyberpunk: {error}", file=sys.stderr)
        sys.exit(1)
