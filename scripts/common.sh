#!/usr/bin/env bash
set -euo pipefail

PROJECT=$(realpath -e "$(dirname "${BASH_SOURCE[0]}")/..")
THEME_LINK="$HOME/.config/omarchy/themes/cyberpunk"
PLUGIN_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-menu"
POLKIT_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-polkit"
NOTIFY_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-notifications"
OSD_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-osd"
LOCK_LINK="$HOME/.config/omarchy/plugins/lightqv.cyberpunk-lock"
HOOK_LINK="$HOME/.config/omarchy/hooks/theme-set.d/lightqv-cyberpunk-menu"
BOOT_LINK="$HOME/.config/omarchy/hooks/post-boot.d/lightqv-cyberpunk-menu"
THEME_SOURCE="$PROJECT/theme"
PLUGIN_SOURCE="$PROJECT/menu-plugin"
POLKIT_SOURCE="$PROJECT/polkit-plugin"
NOTIFY_SOURCE="$PROJECT/notifications-plugin"
OSD_SOURCE="$PROJECT/osd-plugin"
LOCK_SOURCE="$PROJECT/lock-plugin"
HOOK_SOURCE="$PROJECT/hooks/theme-set.d/cyberpunk-menu"
BOOT_SOURCE="$PROJECT/hooks/post-boot.d/cyberpunk-menu"
CLI_LINK="$HOME/.local/bin/cyberpunk"
CLI_SOURCE="$PROJECT/scripts/cyberpunk"
PREFERENCES="${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-cyberpunk/preferences.json"
PLUGIN_ID=lightqv.cyberpunk-menu
POLKIT_ID=lightqv.cyberpunk-polkit
NOTIFY_ID=lightqv.cyberpunk-notifications
OSD_ID=lightqv.cyberpunk-osd
LOCK_ID=lightqv.cyberpunk-lock
STATE_DIR="$PROJECT/.state"
SAFE_MODE="$STATE_DIR/safe-mode"
LOCK_PREF="$STATE_DIR/lock-preference"
LOCK_TRIAL="$STATE_DIR/lock-trial"
LOCK="${XDG_RUNTIME_DIR:-/tmp}/lightqv-cyberpunk-lifecycle.lock"
OPERATION_LOCK="$LOCK.operation"

# Separate from reconciliation: theme hooks need the reconciliation lock while
# an install/removal is in progress. Serialize lifecycle commands without holding
# that lock across a native theme change.
lifecycle_lock() {
  exec 7>"$OPERATION_LOCK"
  flock -n 7 || die "another install/removal is running"
}

die() { printf 'Cyberpunk: %s\n' "$*" >&2; exit 1; }
owned_link() { [[ -L $1 && $(readlink -- "$1") == "$2" ]]; }
unoccupied() { [[ ! -e $1 && ! -L $1 ]]; }
installed() {
  owned_link "$THEME_LINK" "$THEME_SOURCE" &&
    owned_link "$PLUGIN_LINK" "$PLUGIN_SOURCE" &&
    owned_link "$POLKIT_LINK" "$POLKIT_SOURCE" &&
    owned_link "$NOTIFY_LINK" "$NOTIFY_SOURCE" &&
    owned_link "$OSD_LINK" "$OSD_SOURCE" &&
    owned_link "$LOCK_LINK" "$LOCK_SOURCE" &&
    owned_link "$HOOK_LINK" "$HOOK_SOURCE" &&
    owned_link "$BOOT_LINK" "$BOOT_SOURCE" &&
    "$PROJECT/scripts/manage-bashrc.py" check
}
current_theme() { tr -d '\n' <"$HOME/.local/state/omarchy/current/theme.name"; }
install_cli() {
  if ! unoccupied "$CLI_LINK"; then
    owned_link "$CLI_LINK" "$CLI_SOURCE" || die "command path occupied: $CLI_LINK"
    return
  fi
  mkdir -p "$(dirname "$CLI_LINK")"
  ln -s "$CLI_SOURCE" "$CLI_LINK"
}
lock_enabled() {
  if ! unoccupied "$PREFERENCES"; then
    local values
    values=$(python -B "$PROJECT/scripts/preferences.py" read) || die 'invalid component preferences'
    [[ $(jq -r .lock <<<"$values") == true ]]
    return
  fi
  if unoccupied "$LOCK_PREF"; then return 0; fi
  [[ -f $LOCK_PREF && ! -L $LOCK_PREF && $(stat -c %u "$LOCK_PREF") == "$EUID" ]] || die "untrusted lock preference"
  case $(<"$LOCK_PREF") in enabled) return 0 ;; disabled) return 1 ;; *) die "invalid lock preference" ;; esac
}
lock_allowed() {
  if [[ ! -e $SAFE_MODE && ! -L $SAFE_MODE ]]; then return 0; fi
  [[ -f $SAFE_MODE && ! -L $SAFE_MODE ]] || return 1
  [[ -f $LOCK_TRIAL && ! -L $LOCK_TRIAL && $(stat -c %u -- "$LOCK_TRIAL") == "$EUID" && $(<"$LOCK_TRIAL") == lock ]]
}
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
lock_referenced() {
  jq -e --arg id "$LOCK_ID" '
    any(.plugins[]?; .id == $id)
    or any(.disabledPlugins[]?; . == $id)
    or any(.cloneSourceRestores[]?; . == $id)
  ' "$(shell_config)" >/dev/null
}
lock_unlocked() {
  local state result
  state=$(omarchy-shell lock status 2>/dev/null) || return 1
  jq -e '.locked == false and .requested == false and .sessionLocked == false and .secure == false and .passwordPam == true' <<<"$state" >/dev/null || return 1
  if omarchy-hyprland-session-locked; then return 1; else result=$?; fi
  [[ $result == 1 ]]
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
