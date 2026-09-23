#!/usr/bin/env bash
set -euo pipefail

PROJECT=$(realpath -e "$(dirname "${BASH_SOURCE[0]}")/..")
THEME_LINK="$HOME/.config/omarchy/themes/cyberpunk"
PLUGIN_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-menu"
POLKIT_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-polkit"
NOTIFY_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-notifications"
OSD_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-osd"
HOOK_LINK="$HOME/.config/omarchy/hooks/theme-set.d/lightqv-cyberpunk-menu"
BOOT_LINK="$HOME/.config/omarchy/hooks/post-boot.d/lightqv-cyberpunk-menu"
THEME_SOURCE="$PROJECT/theme"
PLUGIN_SOURCE="$PROJECT/menu-plugin"
POLKIT_SOURCE="$PROJECT/polkit-plugin"
NOTIFY_SOURCE="$PROJECT/notifications-plugin"
OSD_SOURCE="$PROJECT/osd-plugin"
HOOK_SOURCE="$PROJECT/hooks/theme-set.d/cyberpunk-menu"
BOOT_SOURCE="$PROJECT/hooks/post-boot.d/cyberpunk-menu"
PLUGIN_ID=lightqv.cyberpunk-menu
POLKIT_ID=lightqv.cyberpunk-polkit
NOTIFY_ID=lightqv.cyberpunk-notifications
OSD_ID=lightqv.cyberpunk-osd
STATE_DIR="$PROJECT/.state"
LOCK="${XDG_RUNTIME_DIR:-/tmp}/lightqv-cyberpunk-lifecycle.lock"

die() { printf 'Cyberpunk: %s\n' "$*" >&2; exit 1; }
owned_link() { [[ -L $1 && $(readlink -- "$1") == "$2" ]]; }
unoccupied() { [[ ! -e $1 && ! -L $1 ]]; }
installed() {
  owned_link "$THEME_LINK" "$THEME_SOURCE" &&
    owned_link "$PLUGIN_LINK" "$PLUGIN_SOURCE" &&
    owned_link "$POLKIT_LINK" "$POLKIT_SOURCE" &&
    owned_link "$NOTIFY_LINK" "$NOTIFY_SOURCE" &&
    owned_link "$OSD_LINK" "$OSD_SOURCE" &&
    owned_link "$HOOK_LINK" "$HOOK_SOURCE" &&
    owned_link "$BOOT_LINK" "$BOOT_SOURCE" &&
    "$PROJECT/scripts/manage-bashrc.py" check
}
current_theme() { tr -d '\n' <"$HOME/.local/state/omarchy/current/theme.name"; }
shell_config() { printf '%s' "$HOME/.config/omarchy/shell.json"; }
clone_referenced() {
  jq -e --arg id "$PLUGIN_ID" '
    any(.bar.layout[]?[]?; (if type == "object" then .id else . end) == $id)
    or any(.plugins[]?; .id == $id)
    or any(.disabledPlugins[]?; . == $id)
    or any(.cloneSourceRestores[]?; . == $id)
  ' "$(shell_config)" >/dev/null
}
polkit_referenced() {
  jq -e --arg id "$POLKIT_ID" '
    any(.plugins[]?; .id == $id)
    or any(.disabledPlugins[]?; . == $id)
    or any(.cloneSourceRestores[]?; . == $id)
  ' "$(shell_config)" >/dev/null
}
notify_referenced() {
  jq -e --arg id "$NOTIFY_ID" '
    any(.plugins[]?; .id == $id)
    or any(.disabledPlugins[]?; . == $id)
    or any(.cloneSourceRestores[]?; . == $id)
  ' "$(shell_config)" >/dev/null
}
osd_referenced() {
  jq -e --arg id "$OSD_ID" '
    any(.plugins[]?; .id == $id)
    or any(.disabledPlugins[]?; . == $id)
    or any(.cloneSourceRestores[]?; . == $id)
  ' "$(shell_config)" >/dev/null
}
menu_enabled() {
  omarchy plugin list --json | jq -e --arg id "$1" 'any(.[]; .id == $id and .enabled == true)' >/dev/null
}
wait_for_menu() {
  local attempt
  for (( attempt=0; attempt<30; attempt++ )); do
    if [[ $(omarchy menu ping 2>/dev/null) == ok ]]; then return 0; fi
    sleep 0.2
  done
  return 1
}
