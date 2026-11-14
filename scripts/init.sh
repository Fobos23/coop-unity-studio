#!/bin/bash
# Copies the studio's project templates into a Unity project, filling the placeholders. Never overwrites a file.
#   bash init.sh <project> <GameName> [--ns <CSharpNamespace>] [--players <max>] [--dry]
# GameName is the product/exe name (Builds/Windows/<GameName>.exe) and the folder Assets/<GameName>/Scripts.
# Copies: CLAUDE.md (if one exists: CLAUDE.studio.md next to it, merge by hand), .claude/agents/*, docs/*,
# Tools/dev/* (autotest, run-suite, recompile, logic tests, dialogs, publish, githooks), C# harness into
# Assets/<GameName>/Scripts/{Dev,Net}. Adds "*.sh text eol=lf" to .gitattributes if missing.
# After it: bash Tools/dev/githooks/install.sh; bash Tools/dev/githooks/pre-commit.test.sh; recompile in the editor.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
T="$SKILL/templates"
P=$1; GAME=$2; shift 2 || { sed -n '2,8p' "$0"; exit 2; }
[ -n "$P" ] && [ -n "$GAME" ] || { sed -n '2,8p' "$0"; exit 2; }
NS=$GAME; PLAYERS=4; DRY=""
while [ $# -gt 0 ]; do
  case $1 in
    --ns) NS=$2; shift 2 ;;
    --players) PLAYERS=$2; shift 2 ;;
    --dry) DRY=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
[ -d "$P/Assets" ] || { echo "no Assets folder in $P: create the Unity project first (unity projects new …)" >&2; exit 2; }
echo "$GAME" | grep -qE '^[A-Za-z][A-Za-z0-9_]*$' || { echo "GameName must be a C#-safe identifier: $GAME" >&2; exit 2; }
echo "$NS" | grep -qE '^[A-Za-z][A-Za-z0-9_.]*$' || { echo "namespace must be a C# identifier: $NS" >&2; exit 2; }

copied=0; skipped=0
put() {   # put <template file> <destination>
  local src=$1 dst=$2
  if [ -e "$dst" ]; then skipped=$((skipped+1)); echo "  keep    ${dst#$P/}"; return; fi
  copied=$((copied+1)); echo "  create  ${dst#$P/}"
  [ -n "$DRY" ] && return
  mkdir -p "$(dirname "$dst")"
  sed -e "s/__GAME__/$GAME/g" -e "s/__NS__/$NS/g" -e "s/__PLAYERS__/$PLAYERS/g" "$src" > "$dst"
}

echo "Project: $P · game $GAME · namespace $NS · players $PLAYERS${DRY:+ · dry run}"
if [ ! -e "$P/CLAUDE.md" ]; then put "$T/CLAUDE.md" "$P/CLAUDE.md"
elif grep -q 'coop-unity-studio' "$P/CLAUDE.md"; then skipped=$((skipped+1)); echo "  keep    CLAUDE.md (already has the studio rules)"
else put "$T/CLAUDE.md" "$P/CLAUDE.studio.md"; echo "  (CLAUDE.md exists: merge CLAUDE.studio.md into it)"; fi
for f in "$T"/agents/*.md; do put "$f" "$P/.claude/agents/$(basename "$f")"; done
for f in "$T"/docs/*.md; do b=$(basename "$f"); put "$f" "$P/docs/${b}"; done
while read -r rel; do put "$T/Tools/dev/$rel" "$P/Tools/dev/${rel#./}"; done < <(cd "$T/Tools/dev" && find . -type f | sort)
for f in "$T"/unity/Dev/*.cs; do put "$f" "$P/Assets/$GAME/Scripts/Dev/$(basename "$f")"; done
for f in "$T"/unity/Net/*.cs; do put "$f" "$P/Assets/$GAME/Scripts/Net/$(basename "$f")"; done

if ! grep -qs 'art/refs' "$P/.gitignore"; then
  echo "  append  .gitignore: reference images, boards and gauntlet images stay out of git"
  [ -n "$DRY" ] || cat >> "$P/.gitignore" <<'EOF'

# Style references and boards are a private moodboard (refs.py, board.py): only their json goes into git.
/art/refs/**
!/art/refs/**/
!/art/refs/**/sources.json
/art/boards/**
!/art/boards/**/
!/art/boards/**/board.json
!/art/boards/**/feedback.json
# Gauntlet: ledgers and verdicts go into git, images and blind pairs do not.
/art/gauntlet/**/*.png
/art/gauntlet/**/*.jpg
/art/gauntlet/**/ab/
EOF
fi
if ! grep -qs '^\*\.sh .*eol=lf' "$P/.gitattributes"; then
  echo "  append  .gitattributes: *.sh text eol=lf"
  [ -n "$DRY" ] || printf '\n# bash scripts must stay LF (core.autocrlf=true breaks them)\n*.sh text eol=lf\n' >> "$P/.gitattributes"
fi
echo "created $copied, kept $skipped existing"
echo "next: cd $P && bash Tools/dev/githooks/install.sh && bash Tools/dev/githooks/pre-commit.test.sh"
echo "      then bash Tools/dev/recompile.sh in the open editor (asmdefs, if the game uses them, must reference"
echo "      Unity.Netcode.Runtime, Unity.Networking.Transport, Unity.Collections)"
