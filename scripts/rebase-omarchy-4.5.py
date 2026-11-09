#!/usr/bin/env python3
"""Reproduce the reviewed 4.5 port from pinned old/new Omarchy source trees.

This is checkout tooling, never an installer or a way to accept arbitrary source
hashes. Both inputs must match the committed compatibility inventories. Generated
files remain reviewable in Git; authentication changes stay upstream-owned.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "b27f932121271a31e8d8b731bc90843d1d6b72b7"


def previous(name):
    return subprocess.check_output(["git", "show", f"{PREVIOUS}:{name}"], cwd=ROOT).decode()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Reviewed replacement no longer unique: {old[:90]!r}")
    return text.replace(old, new, 1)


def checked_source(root, name, inventory):
    data = (root / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != inventory["files"][name]:
        raise ValueError(f"Unreviewed input: {root / name}")
    return data.decode()


def merge_menu(old, new):
    """Keep HUD geometry, incorporating upstream routing, guards and input fixes."""
    with tempfile.TemporaryDirectory(prefix="cyberpunk-merge-") as temporary:
        paths = [Path(temporary) / name for name in ("ours", "base", "theirs")]
        for path, content in zip(paths, (previous("menu-plugin/Menu.qml"), old, new)):
            path.write_text(content)
        result = subprocess.run(["git", "merge-file", "-p", *map(str, paths)],
                                capture_output=True, text=True)
    if result.returncode != 11:
        raise ValueError(f"Expected the 11 reviewed menu conflicts, got {result.returncode}")
    index = 0

    def resolve(match):
        nonlocal index
        index += 1
        ours, theirs = match.groups()
        if index in (1, 2, 9):
            return ours
        if index == 3:
            # Keep the wheel animation, but never land on an installed/disabled row.
            return ours[:ours.index("    if (!cursorActive)")] + theirs
        if index == 4:
            return ours.replace('nextMode === "input" ? "Input" : "Select"',
                                'nextMode === "input" ? Commons.I18n.t("menu.inputPrompt") : Commons.I18n.t("menu.selectPrompt")')
        if index == 5:
            return theirs + ours
        if index == 6:
            return theirs
        if index == 7:
            # Cyberpunk already implements wheel input; do not install a second handler.
            return ours
        if index == 8:
            return "              opacity: row.disabled ? 0.4 : 1\n" + ours
        if index == 10:
            return ours.replace("cursorShape: Qt.PointingHandCursor",
                                "cursorShape: row.disabled ? Qt.ArrowCursor : Qt.PointingHandCursor")
        if index == 11:
            return ours.replace("                   root.resetWheel()",
                                "                   if (row.disabled) return\n                   root.resetWheel()")
        raise ValueError("Unexpected conflict")

    text = re.sub(r"^<<<<<<<[^\n]*\n(.*?)^=======\n(.*?)^>>>>>>>[^\n]*\n",
                  resolve, result.stdout, flags=re.M | re.S)
    if index != 11 or re.search(r"^(<<<<<<<|=======|>>>>>>>)", text, re.M):
        raise ValueError("Unresolved menu conflict")
    text = once(text, "  onFilterTextChanged: if (filterInput.text !== filterText) filterInput.text = filterText\n", "")
    text = once(text, "  onFilterTextChanged: {\n", "  onFilterTextChanged: {\n    if (filterInput.text !== filterText) filterInput.text = filterText\n")
    # The wheel's buffered rows must carry the new disabled role too.
    text = text.replace('record = { sourceIndex: -1,', 'record = { disabled: true, sourceIndex: -1,')
    text = text.replace('record = { sourceIndex: at,', 'record = { disabled: row.disabled === true, sourceIndex: at,')
    # The header gained an input field upstream while Cyberpunk split it into
    # telemetry/title/search. Retain those three regions and put the native IME
    # input on the search line, not on either decorative heading.
    original = previous("menu-plugin/Menu.qml")
    header_start = '        Rectangle {\n          width: parent.width\n          height: root.headerHeight\n'
    header_end = '        Item {\n          width: parent.width\n          height: root.visibleRowsHeight\n'
    start = original.index(header_start, original.index('        id: cardBody'))
    end = original.index(header_end, start)
    header = original[start:end]
    search_line = '          Text {\n            textFormat: Text.PlainText\n            anchors.left: parent.left\n            anchors.right: parent.right\n            anchors.bottom: parent.bottom\n'
    header = once(header, search_line,
        '          FilterInput {\n'
        '            id: filterInput\n'
        '            keyHandler: keyCatcher\n'
        '            anchors.left: parent.left\n'
        '            anchors.right: parent.right\n'
        '            anchors.bottom: parent.bottom\n'
        '            readOnly: root.deleteConfirmOpen\n'
        '            color: root.foreground\n'
        '            font.family: root.scannerFont\n'
        '            font.pixelSize: Style.font.bodySmall\n'
        '            horizontalAlignment: root.mirroredBindings ? Text.AlignRight : Text.AlignLeft\n'
        '            onTextChanged: if (text !== root.filterText) root.setFilter(text)\n'
        '          }\n\n' + search_line)
    header = once(header, '             visible: root.scannerActive || root.dmenuActive\n            color: root.filterText',
                  '             visible: !root.filterText && !filterInput.preeditText\n            color: root.filterText')
    start = text.index(header_start, text.index('        id: cardBody'))
    end = text.index(header_end, start)
    text = text[:start] + header + text[end:]
    text = text.replace('itemId: "dmenu.apply", disabled: false,',
                        'itemId: "dmenu.apply", sourceIndex: displayModel.count, disabled: false,')
    # The custom wheel uses source indices; upstream settleCursor still applies to displayModel.
    return text


def port_polkit():
    # The upstream 4.5 diff changes localization/RTL/animation timing, not the
    # Polkit flow. Keep Cyberpunk's native-flow presentation, with those fixes.
    text = previous("polkit-plugin/PolkitAgent.qml")
    text = once(text, 'import qs.Commons\n', 'import qs.Commons\nimport qs.Commons as Commons\n')
    text = re.sub(r"\bColor\.", "Commons.Color.", text)
    text = once(text, 'function authorizationLabel(message) { return PolkitModel.authorizationLabel(message) }',
                'function authorizationLabel(message) { return message ? PolkitModel.authorizationLabel(message, I18n.t) : I18n.t("polkit.authenticationNeeded") }')
    text = once(text, 'currentMessage = String(flow.message || "Authentication is needed...")',
                'currentMessage = String(flow.message || "")')
    text = once(text, '    id: panel\n', '    id: panel\n'
                '    Binding { target: panel.contentItem; property: "LayoutMirroring.enabled"; value: Commons.I18n.rightToLeft }\n'
                '    Binding { target: panel.contentItem; property: "LayoutMirroring.childrenInherit"; value: true }\n')
    return text


def port_osd():
    text = previous("osd-plugin/Osd.qml")
    text = once(text, 'import qs.Commons\n', 'import qs.Commons\nimport qs.Commons as Commons\nimport qs.Ui\n')
    text = re.sub(r"\bColor\.", "Commons.Color.", text)
    text = once(text, 'rawProgressText, rawDuration)\n    var alreadyVisible',
                'rawProgressText, rawDuration, Commons.I18n.formatNumber)\n    var alreadyVisible')
    text = once(text, "  IpcHandler {", "  ShellIpc {")
    text = once(text, '  PanelWindow {\n    id: panel\n    visible: root.opened\n'
                '    anchors { top: true; bottom: true; left: true; right: true }\n    color: "transparent"\n',
                '  OverlayWindow {\n    id: panel\n    shown: root.opened\n    shownKeyboardFocus: WlrKeyboardFocus.None\n')
    text = once(text, '    WlrLayershell.layer: WlrLayer.Overlay\n'
                '    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None\n    exclusionMode: ExclusionMode.Ignore\n', '')
    return text


def port_toast(text):
    # All delivery, privacy, code/link handling and action execution stay native.
    text = once(text, '    radius: Style.cornerRadius\n    color: Commons.Color.notifications.background\n'
                '    borderSpec: Border.surfaceSpec("notifications", "border", Commons.Color.notifications.border,\n'
                '                                   Math.max(1, Style.space(2)))\n',
                '    radius: 0\n    color: "transparent"\n    borderSpec: Border.none()\n'
                '    CyberpunkFrame { anchors.fill: parent; accent: card.accentColor }\n')
    text = once(text, 'leftMargin: plate.contentLeftInset + Style.space(12)',
                'leftMargin: plate.contentLeftInset + Style.space(70)')
    text = text.replace('font.family: "Liberation Sans"', 'font.family: "JetBrainsMono Nerd Font"')
    return text


def outputs(old_root, new_root):
    old_inventory = json.loads(previous("scripts/omarchy-baseline.json"))
    inventory = json.loads((ROOT / "scripts/omarchy-baseline.json").read_text())
    if inventory["packageVersion"] != "4.5.0-3":
        raise ValueError("This reviewed generator is only for Omarchy 4.5.0-3")
    old_menu = checked_source(old_root, "shell/plugins/menu/Menu.qml", old_inventory)
    result = {}
    for source, destination in inventory["copies"].items():
        native = checked_source(new_root, source, inventory)
        if destination == "menu-plugin/Menu.qml":
            content = merge_menu(old_menu, native)
        elif destination == "menu-plugin/BarWidget.qml":
            content = native.replace('moduleName: "omarchy.menu"', 'moduleName: "lightqv.cyberpunk-menu"')
        elif destination == "menu-plugin/LocalAppLibrary.qml":
            content = native
        elif destination == "polkit-plugin/PolkitAgent.qml":
            content = port_polkit()
        elif destination == "osd-plugin/Osd.qml":
            content = port_osd()
        elif destination == "notifications-plugin/Toast.qml":
            content = port_toast(native)
        elif destination == "notifications-plugin/Service.qml":
            content = once(native, 'readonly property int notificationWidth: Style.space(380)',
                           'readonly property int notificationWidth: Style.space(550)')
        elif destination.startswith("lock-plugin/") and destination.endswith(("Service.qml", "StockLockView.qml")):
            continue  # Generated by the independently pinned build-lock tool.
        else:
            content = native
        result[ROOT / destination] = content
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-root", type=Path, required=True)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs(args.old_root, args.new_root)
    for path, content in generated.items():
        if args.check:
            if not path.is_file() or path.read_text() != content:
                raise ValueError(f"Generated file differs: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(f"{'Checked' if args.check else 'Generated'} {len(generated)} reviewed 4.5 files")


if __name__ == "__main__":
    main()
