#!/bin/bash
# Installs the pre-commit hook shared by all worktrees of the repository (they share one hooks folder).
# The shim only runs Tools/dev/githooks/pre-commit.sh of the branch being committed: branches without it commit as before.
# LFS hooks (pre-push, post-checkout, post-commit, post-merge) are not touched. Safe to rerun.
set -e
hooks=$(git config --get core.hooksPath || true)
[ -n "$hooks" ] || hooks="$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
dst="$hooks/pre-commit"
mark="studio-pre-commit"
if [ -f "$dst" ] && ! grep -q "$mark" "$dst"; then
  echo "$dst already holds another pre-commit — not touching it. Add a call of Tools/dev/githooks/pre-commit.sh to it by hand." >&2
  exit 1
fi
mkdir -p "$hooks"
cat > "$dst" <<'EOF'
#!/bin/sh
# studio-pre-commit (installed by Tools/dev/githooks/install.sh): the checks live in the branch; old branches have none.
h="$(git rev-parse --show-toplevel)/Tools/dev/githooks/pre-commit.sh"
[ -f "$h" ] || exit 0
exec bash "$h"
EOF
chmod +x "$dst"
echo "pre-commit installed: $dst"
