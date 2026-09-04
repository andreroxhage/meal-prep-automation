#!/usr/bin/env bash
# PostToolUse-hook: normaliserar och validerar receptfiler efter Write/Edit.
#
# Exit 0 = filen foljer receptstandarden och andrades inte.
# Exit 2 = stderr skickas tillbaka till Claude, antingen for att filen
#          normaliserades pa disk eller for att det finns FEL att ratta.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
payload="$(cat)"
file_path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // empty')"

[ -z "$file_path" ] && exit 0
[ -f "$file_path" ] || exit 0

# Bara receptfiler. Ovriga filer passerar rort.
base="$(basename "$file_path")"
case "$base" in
  recept-*.md|04-alla-recept.md) ;;
  *.md)
    case "$file_path" in
      */recipe/*|recipe/*) ;;
      *) exit 0 ;;
    esac
    ;;
  *) exit 0 ;;
esac

output="$(python3 "$PROJECT_DIR/.claude/hooks/validate_recipe.py" --fix "$file_path" 2>&1)"
status=$?

if [ "$status" -eq 0 ] && [ -z "$output" ]; then
  exit 0
fi

{
  echo "Receptstandarden (.claude/rules/recipe-style.md) kontrollerade $base:"
  echo "$output"
  if [ "$status" -eq 0 ]; then
    echo
    echo "Inga FEL kvarstår. Rader märkta RÄTTAT är redan ändrade på disk —"
    echo "läs filen igen innan du redigerar den vidare."
  fi
} >&2

exit 2
