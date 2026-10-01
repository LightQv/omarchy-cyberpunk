# Sourced only in interactive Bash sessions. Scripts and direct /usr/bin/sudo
# are untouched. Existing shells follow theme changes on their next invocation.
sudo() {
  if [[ $- != *i* || ! -t 0 || ! -t 1 || -z ${WAYLAND_DISPLAY:-} || ! -r $HOME/.local/state/omarchy/current/theme.name ]] ||
    [[ $(<"$HOME/.local/state/omarchy/current/theme.name") != cyberpunk ]]; then
    command sudo "$@"
    return $?
  fi

  # Explicit stdin/noninteractive/askpass options belong to the caller. Don't
  # convert them, including combined short options, or commands after --.
  local arg
  for arg in "$@"; do
    case "$arg" in
      --) break ;;
      --non-interactive|--stdin|--askpass)
        command sudo "$@"
        return $?
        ;;
      -*)
        if [[ $arg != --* && $arg =~ [nSA] ]]; then
          command sudo "$@"
          return $?
        fi
        ;;
      *) break ;;
    esac
  done

  local askpass
  askpass=$(realpath -m -- "$(dirname -- "${BASH_SOURCE[0]}")/../askpass/cyberpunk-askpass")
  if [[ ! -x $askpass ]]; then
    command sudo "$@"
    return $?
  fi
  SUDO_ASKPASS="$askpass" command sudo -A "$@"
}
