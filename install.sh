#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE="$ROOT/skills/b72-o200k/SKILL.md"
TARGET="both"
DRY_RUN=0

usage() {
  printf '%s\n' \
    'Install B72-o200k for Codex and/or Hermes.' \
    'Usage: ./install.sh [--only codex|hermes|both] [--dry-run]'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --only) TARGET="${2:?missing value for --only}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$TARGET" in codex|hermes|both) ;; *) printf 'Invalid target: %s\n' "$TARGET" >&2; exit 2 ;; esac
[ -f "$SOURCE" ] || { printf 'Missing skill: %s\n' "$SOURCE" >&2; exit 1; }

install_one() {
  name="$1"
  destination="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '%s -> %s\n' "$SOURCE" "$destination"
  else
    mkdir -p "$(dirname -- "$destination")"
    cp "$SOURCE" "$destination"
    printf 'Installed %s\n' "$destination"
  fi
}

if [ "$TARGET" = codex ] || [ "$TARGET" = both ]; then
  install_one codex "${CODEX_HOME:-$HOME/.codex}/skills/b72-o200k/SKILL.md"
fi
if [ "$TARGET" = hermes ] || [ "$TARGET" = both ]; then
  install_one hermes "${HERMES_HOME:-$HOME/.hermes}/skills/software-development/b72-o200k/SKILL.md"
fi

printf '%s\n' 'Restart the agent after installation so it reloads its skill index.'
