#!/usr/bin/env bash
# SubagentStop-hook: slapper inte igenom en subagent som lamnar receptfiler
# som bryter mot receptstandarden.
#
# Exit 2 skickar agenten tillbaka till arbetet med felen som motivering.
# En rakneraknare tillater max MAX_BLOCKS blockeringar per agent, sa att en
# agent som inte klarar att ratta felen inte fastnar i en oandlig loop.
set -uo pipefail

MAX_BLOCKS=2
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
payload="$(cat)"
agent_id="$(printf '%s' "$payload" | jq -r '.agent_id // .session_id // "okand"')"
state_dir="${TMPDIR:-/tmp}/meal-prep-recipe-gate"
mkdir -p "$state_dir"
counter="$state_dir/$(printf '%s' "$agent_id" | tr -c 'A-Za-z0-9_.-' '_')"

cd "$PROJECT_DIR" || exit 0

# Receptfiler som agenten har skapat eller andrat.
mapfile -t files < <(
  git status --porcelain --untracked-files=all 2>/dev/null \
    | sed 's/^...//' \
    | grep -E '(^|/)(recept-[^/]*\.md|04-alla-recept\.md)$|^recipe/.*\.md$' \
    | sort -u
)
[ "${#files[@]}" -eq 0 ] && exit 0

output="$(python3 "$PROJECT_DIR/.claude/hooks/validate_recipe.py" --quiet "${files[@]}" 2>&1)"
[ $? -eq 0 ] && { rm -f "$counter"; exit 0; }

blocks=$(( $(cat "$counter" 2>/dev/null || echo 0) + 1 ))
echo "$blocks" > "$counter"

if [ "$blocks" -gt "$MAX_BLOCKS" ]; then
  rm -f "$counter"
  {
    echo "Receptstandarden hittar fortfarande fel efter $MAX_BLOCKS försök."
    echo "Släpper igenom agenten — rapportera de kvarstående felen till användaren:"
    echo "$output"
  } >&2
  exit 0
fi

{
  echo "Du är inte klar: receptfilerna bryter mot .claude/rules/recipe-style.md."
  echo "$output"
  echo
  echo "Rätta varje FEL och skriv om filerna innan du avslutar."
} >&2
exit 2
