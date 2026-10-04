#!/usr/bin/env python3
"""Shared first-install selection and a non-installing presentation preview."""

import argparse
import sys

from preferences import COMPONENTS

LABELS = {
    "menu": "Menu and application launcher",
    "notifications": "Notifications",
    "osd": "OSD — volume, brightness, microphone and media",
    "sudo": "Graphical sudo",
    "polkit": "Polkit authentication",
    "lock": "Session-lock presentation (safe-mode gated)",
}


def arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--setup", choices=("base", "full", "custom"))
    group.add_argument("--components", help="Comma-separated component names for an unattended custom setup")
    parser.add_argument("--non-interactive", action="store_true", help="Never prompt; new installations default to base-only")


def ask(terminal, prompt, allowed, default):
    while True:
        print(prompt, end="", flush=True)
        answer = terminal.readline()
        if not answer:
            raise ValueError("Setup cancelled: terminal input ended")
        answer = answer.strip().lower() or default
        if answer in allowed:
            return answer
        print("Choose one of: " + ", ".join(allowed))


def select(setup=None, components=None, non_interactive=False):
    """Return six choices without writing preferences or changing providers."""
    choices = None
    if components is not None:
        names = components.split(",") if components else []
        if any(name not in COMPONENTS for name in names) or len(names) != len(set(names)):
            raise ValueError("Components must be unique names: " + ", ".join(COMPONENTS))
        choices = {name: name in names for name in COMPONENTS}
    terminal = None
    if not non_interactive and sys.stdout.isatty():
        try:
            terminal = open("/dev/tty", encoding="utf-8")
        except OSError:
            pass
    try:
        if choices is None and setup is None and terminal is not None:
            print("Choose your Cyberpunk setup:\n\n"
                  "  1. Base theme only — palette, wallpapers and borders\n"
                  "  2. Full stack — all optional components\n"
                  "  3. Custom — choose individual components\n\n"
                  "Lock choices are saved, but stock lock remains active while safe mode is on.\n")
            setup = {"1": "base", "2": "full", "3": "custom"}[ask(terminal, "Selection [1]: ", ("1", "2", "3"), "1")]
        setup = setup or "base"
        if choices is not None:
            pass
        elif setup == "custom":
            if terminal is None:
                raise ValueError("Custom selection needs a terminal; use --components for unattended installation")
            choices = {name: ask(terminal, f"  {LABELS[name]} [y/N]: ", ("y", "n", "yes", "no"), "n") in ("y", "yes")
                       for name in COMPONENTS}
        else:
            choices = dict.fromkeys(COMPONENTS, setup == "full")
        print("\nRequested setup: " + ", ".join(name for name, enabled in choices.items() if enabled)
              if any(choices.values()) else "\nRequested setup: base theme only")
        if choices["lock"]:
            print("Lock: preference enabled; stock lock stays active while safe mode is on.")
        if terminal is not None and ask(terminal, "Install this setup? [Y/n]: ", ("y", "n", "yes", "no"), "y") in ("n", "no"):
            raise ValueError("Setup cancelled")
        return choices
    finally:
        if terminal is not None:
            terminal.close()


def completion():
    print("\nInspect your setup:       cyberpunk status\n"
          "Change component choices: cyberpunk --help\n")


def main():
    parser = argparse.ArgumentParser(description="Preview installer choices; never download or install")
    arguments(parser)
    args = parser.parse_args()
    print("PREVIEW ONLY — no downloads, preferences or desktop changes.\n")
    choices = select(args.setup, args.components, args.non_interactive)
    print("\nDownloading release… (simulated)\nVerifying archive… (simulated)\nInstalling… (simulated)\n\nCyberpunk installed. (simulated)\n")
    for name, enabled in choices.items():
        provider = "Cyberpunk" if enabled else "Native"
        if name == "lock":
            provider = "Native — safe mode" + ("; preference enabled" if enabled else "")
        print(f"{name.title():<16} {provider}")
    completion()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyboardInterrupt) as error:
        print(f"Preview cancelled: {error}", file=sys.stderr)
        sys.exit(1)
