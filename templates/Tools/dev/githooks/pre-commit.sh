#!/bin/bash
# Pre-commit checks. Installed once for all worktrees: bash Tools/dev/githooks/install.sh. Settings: hook.conf next to it.
# Self-test: bash Tools/dev/githooks/pre-commit.test.sh.
#   net  — the network format changed (RPC, NetworkVariable/NetworkList, serialization, snapshot writers, NetworkObject
#          in a prefab or scene, the network prefab list), so the network version must differ from master's at the
#          branch point (one bump per branch is enough); in a merge where both sides changed the format, from both.
#   mtu  — transport limits (LIMITS in hook.conf) do not grow.
#   junk — editor junk (JUNK in hook.conf) is not committed.
#   bin  — a binary .asset (baked NavMesh, lighting) is not committed as text: under a rule with eol but no text
#          git converts line endings without looking at the content, drops the CR of every CR LF pair inside the
#          data, and Unity refuses to load the shortened file. Such files need a 'binary' line in .gitattributes.
# A false positive: STUDIO_ALLOW="net junk mtu bin" (only the words needed) before git commit. Never --no-verify.
# Past commits: pre-commit.sh --range <old> <new> — the net and mtu checks between two commits.

HERE="$(cd "$(dirname "$0")" && pwd)"
NETVERSION_FILE="Assets/Game/Scripts/Net/GameNet.cs"
LIMITS=""
NET_PREFAB_LISTS=':(glob)Assets/**/*NetworkPrefabs*.asset'
JUNK=()
# Read without carriage returns: a CRLF checkout (core.autocrlf=true) must not put CR characters into the paths.
[ -f "$HERE/hook.conf" ] && . <(tr -d '\r' < "$HERE/hook.conf")

EMPTY=4b825dc642cb6eb9a060e54bf8d69288fbee4904
# An added or removed line with this text in game code (not Editor) changes what goes over the network.
NET_CS='\[Rpc\(|\[(ServerRpc|ClientRpc)|void[[:space:]]+[A-Za-z0-9_]+Rpc[[:space:]]*\(|NetworkVariable<|NetworkList<|NetworkSerialize|\.SerializeValue\(|SerializeNetworkSerializable|(Write|Read)(Value|Bytes)Safe|(Write|Read)ValuePacked|NamedMessage|CustomMessagingManager'
CS_PATHS=(':(glob)Assets/**/*.cs' ':(exclude,glob)**/Editor/**')
ASSET_PATHS=(':(glob)Assets/**/*.prefab' ':(glob)Assets/**/*.unity')

gd() { git -c core.quotepath=off diff --no-color --no-ext-diff "$@"; }
allow() { case " ${STUDIO_ALLOW//,/ } " in *" $1 "*) return 0;; esac; return 1; }
blob() { git show "$1:$2" 2>/dev/null; }                     # $1 — commit, empty — the index
ver() { blob "$1" "$NETVERSION_FILE" | grep -o 'Version = "[^"]*"' | head -1 | cut -d'"' -f2; }
num() { blob "$1" "$2" | grep -oE "$3 = [0-9]+" | head -1 | grep -oE '[0-9]+$'; }
rev() { git rev-parse -q --verify "$1^{commit}" 2>/dev/null; }

# net_why <git diff args> — what in the changes touches the network format (empty — nothing)
net_why() {
  local f
  gd "$@" --name-only -G"$NET_CS" -- "${CS_PATHS[@]}" | while IFS= read -r f; do
    gd "$@" -U0 -- "$f" | grep -E '^[-+]' | grep -vE '^(\+\+\+|---) ' | grep -E -- "$NET_CS" | head -3 | cut -c1-140 | sed "s|^|    $f: |"
  done
  gd "$@" --name-only -G'GlobalObjectIdHash' -- "${ASSET_PATHS[@]}" | sed 's|^|    NetworkObject: |'
  gd "$@" --name-only -- "$NET_PREFAB_LISTS" | sed 's|^|    network prefab list: |'
}

# The version is compared with master at the branch point (origin/master, else local master). One bump per branch is
# enough: its builds already differ from master's; a commit straight on master is compared with the pushed master.
branch_base() {
  local m
  rev HEAD >/dev/null || { echo $EMPTY; return; }
  m=$(rev refs/remotes/origin/master || rev refs/heads/master) || { rev HEAD; return; }
  git merge-base HEAD "$m" 2>/dev/null || echo $EMPTY
}

failed=0
say() { failed=1; printf '%s\n' "$@" >&2; }

if [ "$1" = --range ]; then
  OLD=$(rev "$2") || { echo "no commit $2" >&2; exit 2; }
  NEW=$(rev "$3") || { echo "no commit $3" >&2; exit 2; }
  BASE=$OLD; NEWSPEC=$NEW; MTUBASE=$OLD; DIFF=("$OLD" "$NEW"); MERGE=""
else
  BASE=$(branch_base); NEWSPEC=""; MTUBASE=$(rev HEAD || echo $EMPTY); DIFF=(--cached "$BASE")
  MERGE=$(rev MERGE_HEAD)
fi

# --- net: the version when the network format changed
why=$(net_why "${DIFF[@]}")
v=$(ver "$NEWSPEC"); vb=$(ver "$BASE")
[ -n "$OLD" ] && echo "net=$([ -n "$why" ] && echo 1 || echo 0) version=$vb->$v"
if ! allow net; then
  if [ -n "$why" ] && [ "$v" = "$vb" ]; then
    say "✖ The network format changed, but the network version is $v, as on master at the branch point ${BASE:0:8}." \
        "  What changed:" "$why" \
        "  Bump Version in $NETVERSION_FILE and add to its comment what changed." \
        "  The format really did not change — STUDIO_ALLOW=net git commit …" ""
  fi
  if [ -n "$MERGE" ]; then
    mb=$(git merge-base HEAD "$MERGE")
    if [ -n "$(net_why "$mb" HEAD | head -1)" ] && [ -n "$(net_why "$mb" "$MERGE" | head -1)" ]; then
      vh=$(ver HEAD); vm=$(ver "$MERGE")
      if [ "$v" = "$vh" ] || [ "$v" = "$vm" ]; then
        say "✖ Merge: the network format changed on both sides, and the resulting version $v equals one of them" \
            "  (HEAD $vh, MERGE_HEAD $vm). Builds of that branch would count as compatible with the merge — use a version above both." ""
      fi
    fi
  fi
fi

# --- mtu: transport limits do not grow
if ! allow mtu; then
  for pair in $LIMITS; do
    file=${pair%%:*}; const=${pair##*:}
    o=$(num "$MTUBASE" "$file" "$const"); nw=$(num "$NEWSPEC" "$file" "$const")
    if [ -n "$o" ] && [ -n "$nw" ] && [ "$nw" -gt "$o" ]; then
      say "✖ $const grew from $o to $nw ($file). Through a relay bigger packets are lost — the limits never grow." \
          "  On purpose — STUDIO_ALLOW=mtu git commit …" ""
    fi
  done
fi

# --- junk: editor junk (only on a real commit)
if [ -z "$OLD" ] && [ ${#JUNK[@]} -gt 0 ] && ! allow junk; then
  junk=$(gd --cached --name-only --diff-filter=AM "$MTUBASE" -- "${JUNK[@]}" | while IFS= read -r f; do
    # in a merge, a file taken as is from the other branch is not this commit's junk
    [ -n "$MERGE" ] && [ "$(git rev-parse -q ":$f" 2>/dev/null)" = "$(git rev-parse -q "$MERGE:$f" 2>/dev/null)" ] && continue
    echo "    $f"
  done)
  if [ -n "$junk" ]; then
    say "✖ Editor junk in the commit:" "$junk" \
        "  Restore it: git restore --staged --worktree -- <file> (a new file — git rm --cached and delete)." \
        "  The change is really needed — STUDIO_ALLOW=junk git commit …" ""
  fi
fi

# --- bin: a binary .asset that git converts as text without looking at it (text set, or eol set without text)
if [ -z "$OLD" ] && ! allow bin; then
  bin=$(gd --cached --name-only --diff-filter=AM "$MTUBASE" -- ':(glob)**/*.asset' | git check-attr --stdin text eol | awk -F': ' '
      { v[$1, $2] = $3; if (!($1 in seen)) { seen[$1] = 1; order[++n] = $1 } }
      END { for (i = 1; i <= n; i++) { p = order[i]; t = v[p, "text"]; e = v[p, "eol"]
            if (t == "set" || (t == "unspecified" && (e == "lf" || e == "crlf"))) print p } }' | while IFS= read -r f; do
    # binary the way git itself decides: a NUL byte in the first 8000 bytes
    size=$(git cat-file -s ":$f" 2>/dev/null) || continue
    [ "$size" -gt 8000 ] && size=8000
    [ "$(git cat-file blob ":$f" 2>/dev/null | head -c 8000 | tr -d '\000' | wc -c)" -lt "$size" ] && echo "    $f"
  done)
  if [ -n "$bin" ]; then
    say "✖ A binary .asset goes into git as text:" "$bin" \
        "  Under a rule with eol and no text git drops the CR of CR LF pairs inside the data: the file gets shorter than" \
        "  its header and Unity does not load it. Add '<name> binary' to .gitattributes, then git add --renormalize -- <file>." \
        "  The file really is text — STUDIO_ALLOW=bin git commit …" ""
  fi
fi

exit $failed
