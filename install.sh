#!/usr/bin/env bash
# Small bootstrap: application code always comes from a checksummed tagged release.
set -euo pipefail
banner() {
  # The supplied UTF-8 Braille artwork is kept literal: no escape processing.
  # Redirected output and narrow/non-UTF-8 terminals get the compact caption.
  local width locale=${LC_ALL:-${LC_CTYPE:-${LANG:-}}}
  width=$(tput cols 2>/dev/null || printf '80')
  if [[ -t 1 && ${TERM:-dumb} != dumb && ${locale,,} == *utf*8* && $width =~ ^[0-9]+$ && $width -ge 61 ]]; then
    if [[ -z ${NO_COLOR+x} ]]; then printf '\033[93m'; fi
    cat <<'LOGO'
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⠀⡔⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⢚⣉⣠⡽⠂⠀⠀⠀⠀⡰⢋⡼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⢴⡆⠀⠀
⠀⠀⠀⠀⠀⢀⡤⠐⢊⣥⠶⠛⠁⢀⠄⡆⣠⠤⣤⠞⢠⠿⢥⡤⠀⠀⠠⢤⠀⠀⠀⠤⠤⠤⡄⢠⠤⠄⠤⠀⠀⠀⠒⣆⡜⣿⣄⠀⡤⢤⠖⣠⣀⠤⢒⣭⠶⠛⠃⠀⠀
⢀⣀⡠⢴⣎⣥⣴⣾⣟⡓⠒⠒⠒⠺⣄⡋⢀⡾⢃⣴⢖⣢⣞⢁⣋⣉⣹⠏⠚⠛⢛⣉⣤⡴⢞⠃⣰⠾⠟⣛⣩⢵⢶⡟⣰⠇⠘⡼⢡⡟⣀⡋⢵⡞⠋⠁⠀⠀⠀⠀⠀
⠈⠢⠄⠤⠤⠤⠤⠤⠴⠤⠴⠶⠶⢾⠟⣱⡿⢤⢿⣕⠾⣿⣿⣩⡭⢤⠞⣰⠶⢤⣀⡉⠓⢾⡍⣠⠴⠾⠛⠹⠡⣟⡁⢰⢏⣼⡇⢰⣿⢀⠟⠳⣤⣌⣦⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⢃⡼⠋⠛⠾⠚⠁⠀⠈⠉⠀⠀⠸⣄⠏⠀⠀⠈⠙⠓⡟⣰⠏⠀⠀⠀⠘⠾⠛⠳⠞⠉⠁⠙⠋⠙⠚⠀⠀⠀⠙⠛⢿⣷⣤⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣜⡵⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⢏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⢿⣕⡄
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣯⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠃
LOGO
    if [[ -z ${NO_COLOR+x} ]]; then printf '\033[0m'; fi
  fi
  printf '\nOMARCHY CYBERPUNK · %s\n\n' "$1"
}
main() {
  for command in curl python sha256sum mktemp; do
    command -v "$command" >/dev/null || { printf 'Missing dependency: %s\n' "$command" >&2; return 1; }
  done
  local version=${1:-} repo=LightQv/omarchy-cyberpunk
  [[ $# -le 1 ]] || { printf 'Usage: install.sh [vX.Y.Z]\n' >&2; return 1; }
  if [[ -z $version ]]; then
    version=$(curl --proto '=https' --tlsv1.2 -fsSL --retry 3 --connect-timeout 15 --max-time 120 \
      "https://api.github.com/repos/$repo/releases/latest" | python -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
  fi
  [[ $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { printf 'Invalid release version\n' >&2; return 1; }
  banner "$version"
  local temporary asset="omarchy-cyberpunk-$version.tar.gz" base="https://github.com/$repo/releases/download/$version"
  temporary=$(mktemp -d)
  trap "rm -rf -- $(printf '%q' "$temporary")" EXIT
  printf 'Downloading Cyberpunk %s…\n' "$version"
  curl --proto '=https' --tlsv1.2 -fsSL --retry 3 --connect-timeout 15 --max-time 300 "$base/$asset" -o "$temporary/$asset"
  curl --proto '=https' --tlsv1.2 -fsSL --retry 3 --connect-timeout 15 --max-time 120 "$base/SHA256SUMS" -o "$temporary/SHA256SUMS"
  printf 'Verifying archive…\n'
  python - "$temporary" "$asset" <<'PY'
import hashlib, pathlib, sys, tarfile
root = pathlib.Path(sys.argv[1]); name = sys.argv[2]
expected = (root / "SHA256SUMS").read_text().strip().split()
if len(expected) != 2 or expected[1] != name or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected[0]:
    raise SystemExit("Release checksum mismatch; nothing installed")
prefix = name.removesuffix(".tar.gz")
with tarfile.open(root / name) as archive:
    members = archive.getmembers()
    if len(members) > 2000 or sum(item.size for item in members) > 200_000_000:
        raise SystemExit("Unexpected release archive size")
    for item in members:
        parts = pathlib.PurePosixPath(item.name).parts
        if not parts or parts[0] != prefix or ".." in parts or not (item.isfile() or item.isdir()):
            raise SystemExit("Unsafe release archive member")
    archive.extractall(root, filter="data")
PY
  printf 'Installing…\n'
  bash "$temporary/${asset%.tar.gz}/install"
  rm -rf -- "$temporary"
  trap - EXIT
  printf '\nReady.\n\n  cyberpunk status\n  cyberpunk enable menu\n\n'
}
main "$@"
