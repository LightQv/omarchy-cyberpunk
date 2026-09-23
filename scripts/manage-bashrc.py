#!/usr/bin/python
"""Add/remove only the exact, owned interactive-sudo stanza in ~/.bashrc."""

import os
from pathlib import Path
import shlex
import stat
import sys
import tempfile

START = "# >>> lightqv cyberpunk interactive sudo >>>"
END = "# <<< lightqv cyberpunk interactive sudo <<<"
PROJECT = Path(__file__).resolve().parent.parent
SOURCE = shlex.quote(str(PROJECT / "scripts" / "interactive-sudo.sh"))
STANZA = f"{START}\n[[ -r {SOURCE} ]] && source {SOURCE}\n{END}\n"
PATH = Path.home() / ".bashrc"


def read() -> str:
    if not PATH.is_file() or PATH.is_symlink():
        raise ValueError("~/.bashrc must be a regular file")
    return PATH.read_text(encoding="utf-8")


def write(content: str) -> None:
    mode = stat.S_IMODE(PATH.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=PATH.parent,
            prefix=".bashrc.cyberpunk.", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(mode)
        temporary.replace(PATH)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"install", "remove", "check", "absent"}:
        raise ValueError("usage: manage-bashrc.py install|remove|check|absent")
    action = sys.argv[1]
    current = read()
    if START in current or END in current:
        if current.count(START) != 1 or current.count(END) != 1 or STANZA not in current:
            raise ValueError("sudo stanza changed; refusing to overwrite unrelated Bash config")
        present = True
    else:
        present = False

    if action == "install" and not present:
        write(current + ("" if current.endswith("\n") else "\n") + "\n" + STANZA)
    elif action == "remove" and present:
        write(current.replace("\n" + STANZA, "", 1))
    elif action == "check" and not present:
        raise ValueError("interactive sudo stanza missing")
    elif action == "absent" and present:
        raise ValueError("interactive sudo stanza still present")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"Cyberpunk: {exc}", file=sys.stderr)
        sys.exit(1)
