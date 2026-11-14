#!/bin/bash
# Self-test of the pre-commit checks: bash Tools/dev/githooks/pre-commit.test.sh
# Every test is a temporary repository with a bare "origin"; the hook runs in it the way git runs it, from a copy
# with its own hook.conf (so the project's settings do not matter here).
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/studiohook.XXXXXX")"
mkdir -p "$WORK/hook"; cp "$HERE/pre-commit.sh" "$WORK/hook/pre-commit.sh"
cat > "$WORK/hook/hook.conf" <<'CONF'
NETVERSION_FILE="Assets/Game/Scripts/Net/GameNet.cs"
LIMITS="Assets/Game/Scripts/Net/TransportDriver.cs:MaxMessage Assets/Game/Scripts/Net/GameNet.cs:NgoMtu"
NET_PREFAB_LISTS=':(glob)Assets/**/*NetworkPrefabs*.asset'
JUNK=("Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF - Fallback.asset"
      Assets/Resources/PerformanceTestRunInfo.json Assets/Resources/PerformanceTestRunInfo.json.meta
      ProjectSettings/PackageManagerSettings.asset)
CONF
HOOK="$WORK/hook/pre-commit.sh"
pass=0; fail=0; n=0; ENVV=""

G() { git -C "$R" "$@" >/dev/null 2>&1; }
w() { mkdir -p "$(dirname "$R/$1")"; printf '%s\n' "$2" > "$R/$1"; G add -- "$1"; }
a() { printf '%s\n' "$2" >> "$R/$1"; G add -- "$1"; }
gamenet() { w Assets/Game/Scripts/Net/GameNet.cs "namespace Game { public static class GameNet {
        public const string Version = \"$1\"; // grows with every network format change
        public const int NgoMtu = ${2:-1088};
} }"; }
transport() { w Assets/Game/Scripts/Net/TransportDriver.cs "class TransportDriver {
        public const int MaxMessage = ${1:-1200};
}"; }
commit() { G commit -q --no-verify -m "${1:-c}"; }
push() { G push -q origin HEAD; }

fresh() {
  n=$((n+1)); R="$WORK/r$n"; ENVV=""
  git init -q --bare -b master "$R.git"; git init -q -b master "$R"
  G config user.name test; G config user.email test@example.invalid
  G config commit.gpgsign false; G config core.autocrlf false
  G remote add origin "$R.git"
  gamenet 0.1.0; transport
  w Assets/Game/Scripts/AI/Enemy.cs "class Enemy {
    void Tick() { }
}"
  w Assets/Game/Scripts/Net/Cargo.cs "class Cargo { }"
  w Assets/Game/Editor/Builder.cs "class Builder { }"
  w Assets/Game/Prefabs/Box.prefab "--- !u!1 &1
GameObject:
  m_Name: Box"
  w Assets/DefaultNetworkPrefabs.asset "List:
- a"
  w "Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF - Fallback.asset" "atlas: 1"
  w ProjectSettings/PackageManagerSettings.asset "x: 1"
  commit init; push
}

# check pass|block "what is checked" [text that must be in the hook message]
check() {
  local want=$1 name=$2 needle=$3 out code ok=1
  out=$(cd "$R" && env $ENVV bash "$HOOK" 2>&1); code=$?
  if [ "$want" = pass ]; then [ $code -eq 0 ] || ok=0
  else [ $code -eq 1 ] || ok=0; [ -z "$needle" ] || printf '%s' "$out" | grep -qF -- "$needle" || ok=0; fi
  if [ $ok -eq 1 ]; then pass=$((pass+1)); echo "ok   $name"
  else fail=$((fail+1)); echo "FAIL $name (exit $code, want $want${needle:+, "$needle"})"; printf '%s\n' "$out" | sed 's/^/     | /'; fi
}

rpc() { a "${1:-Assets/Game/Scripts/AI/Enemy.cs}" "    [Rpc(SendTo.ClientsAndHost)]
    void ${2:-Hit}Rpc(Vector3 at) { }"; }

# --- ordinary changes
fresh; a Assets/Game/Scripts/AI/Enemy.cs "// tweak"; check pass "ordinary code change passes"
fresh; a Assets/Game/Scripts/AI/Enemy.cs "    void Shoot() { HitRpc(transform.position); }"; check pass "Rpc call inside a method body passes"
fresh; rpc Assets/Game/Editor/Builder.cs; check pass "Rpc text in Editor code passes"

# --- network format without a new version
fresh; rpc; check block "new Rpc without version bump is blocked" "network version"
fresh; rpc; gamenet 0.2.0; check pass "new Rpc with version bump passes"
fresh; a Assets/Game/Scripts/AI/Enemy.cs "    public readonly NetworkVariable<byte> Mood = new NetworkVariable<byte>();"; check block "new NetworkVariable is blocked" "Enemy.cs"
fresh; a Assets/Game/Scripts/Net/Cargo.cs "    public NetworkList<int> items;"; check block "new NetworkList is blocked"
fresh; a Assets/Game/Scripts/Net/Cargo.cs "            s.SerializeValue(ref weight);"; check block "serializer field change is blocked"
fresh; a Assets/Game/Scripts/AI/Enemy.cs "                writer.WriteValueSafe(yaw);"; check block "snapshot writer change is blocked"
fresh; a Assets/Game/Prefabs/Box.prefab "  GlobalObjectIdHash: 123456"; check block "prefab gaining a NetworkObject is blocked" "Box.prefab"
fresh; a Assets/DefaultNetworkPrefabs.asset "- b"; check block "network prefab list change is blocked" "DefaultNetworkPrefabs.asset"
fresh; rpc; ENVV="STUDIO_ALLOW=net"; check pass "STUDIO_ALLOW=net lets a same-format change through"

# --- the version is compared with master at the branch point: one bump per branch is enough
fresh; G checkout -q -b feat; rpc; gamenet 0.2.0; commit; rpc Assets/Game/Scripts/Net/Cargo.cs Load; check pass "bump earlier in the branch covers later commits"
fresh; G checkout -q -b feat; rpc; gamenet 0.2.0; commit; push; rpc Assets/Game/Scripts/Net/Cargo.cs Load; check pass "bump in an already pushed branch still covers later commits"
fresh; G checkout -q -b feat; a Assets/Game/Scripts/AI/Enemy.cs "// docs"; commit; push; rpc; check block "branch that never bumped is blocked" "0.1.0"
fresh; rpc; gamenet 0.2.0; commit; push; rpc Assets/Game/Scripts/Net/Cargo.cs Load; check block "commit on master after a pushed bump needs its own bump" "0.2.0"

# --- hook.conf checked out with CRLF (core.autocrlf=true) still works
cp "$WORK/hook/hook.conf" "$WORK/hook/hook.conf.lf"; sed -i 's/$/\r/' "$WORK/hook/hook.conf"
fresh; rpc; gamenet 0.2.0; check pass "CRLF hook.conf: a bumped version is seen"
fresh; rpc; check block "CRLF hook.conf: a missing bump is still blocked" "network version is 0.1.0"
mv -f "$WORK/hook/hook.conf.lf" "$WORK/hook/hook.conf"

# --- editor junk
fresh; a "Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF - Fallback.asset" "atlas: 2"; check block "dirty TMP fallback font is blocked" "LiberationSans SDF - Fallback.asset"
fresh; a "Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF - Fallback.asset" "atlas: 2"; ENVV="STUDIO_ALLOW=junk"; check pass "STUDIO_ALLOW=junk lets the font through"
fresh; w Assets/Resources/PerformanceTestRunInfo.json "{}"; check block "PerformanceTestRunInfo.json is blocked" "PerformanceTestRunInfo.json"
fresh; a ProjectSettings/PackageManagerSettings.asset "y: 2"; check block "PackageManagerSettings change is blocked" "PackageManagerSettings.asset"

# --- transport limits
fresh; gamenet 0.1.0 1400; check block "raising NgoMtu is blocked" "NgoMtu"
fresh; gamenet 0.1.0 1000; check pass "lowering NgoMtu passes"
fresh; transport 1500; check block "raising MaxMessage is blocked" "MaxMessage"

# --- merges
fresh; G checkout -q -b side; rpc; gamenet 0.2.0; commit side; G checkout -q master
rpc Assets/Game/Scripts/Net/Cargo.cs Load; gamenet 0.2.0; commit main; push
G merge --no-commit --no-ff side; check block "merge where both sides took the same version is blocked" "0.2.0"
gamenet 0.3.0; check pass "merge with a fresh version passes"

fresh; G checkout -q -b side; rpc; gamenet 0.3.0; commit side; G checkout -q master
rpc Assets/Game/Scripts/Net/Cargo.cs Load; gamenet 0.2.0; commit main; push
G merge --no-commit --no-ff side; gamenet 0.3.0; check block "merge keeping the other side's version is blocked" "0.3.0"
gamenet 0.4.0; check pass "merge with a version above both passes"

fresh; G checkout -q -b side; rpc; gamenet 0.2.0; commit side; G checkout -q master
a Assets/Game/Scripts/AI/Enemy.cs "// docs"; commit main; push
G merge --no-commit --no-ff side; check pass "merge where only the other side changed the format passes"

# --- past commits (calibration)
fresh; rpc; commit; out=$(cd "$R" && bash "$HOOK" --range HEAD^ HEAD 2>&1); code=$?
if [ $code -eq 1 ]; then pass=$((pass+1)); echo "ok   --range flags a past commit without a bump"
else fail=$((fail+1)); echo "FAIL --range flags a past commit without a bump (exit $code)"; printf '%s\n' "$out" | sed 's/^/     | /'; fi
fresh; rpc; gamenet 0.2.0; commit; out=$(cd "$R" && bash "$HOOK" --range HEAD^ HEAD 2>/dev/null); code=$?
if [ $code -eq 0 ] && printf '%s' "$out" | grep -qx "net=1 version=0.1.0->0.2.0"; then pass=$((pass+1)); echo "ok   --range reports detection and versions"
else fail=$((fail+1)); echo "FAIL --range reports detection and versions (exit $code)"; printf '%s\n' "$out" | sed 's/^/     | /'; fi

# --- a real git commit through the shim of install.sh
fresh; mkdir -p "$R/Tools/dev/githooks"; cp "$HOOK" "$WORK/hook/hook.conf" "$R/Tools/dev/githooks/"
(cd "$R" && bash "$HERE/install.sh") >/dev/null 2>&1
rpc; before=$(git -C "$R" rev-parse HEAD); git -C "$R" commit -q -m blocked >/dev/null 2>&1; after=$(git -C "$R" rev-parse HEAD)
if [ "$before" = "$after" ] && [ -x "$R/.git/hooks/pre-commit" ]; then pass=$((pass+1)); echo "ok   installed hook stops a real git commit"
else fail=$((fail+1)); echo "FAIL installed hook stops a real git commit"; fi
rm -f "$R/Tools/dev/githooks/pre-commit.sh"; git -C "$R" commit -q -m old-branch >/dev/null 2>&1
if [ "$after" != "$(git -C "$R" rev-parse HEAD)" ]; then pass=$((pass+1)); echo "ok   branch without the check commits freely"
else fail=$((fail+1)); echo "FAIL branch without the check commits freely"; fi

rm -rf "$WORK"
echo "pass=$pass fail=$fail"
[ $fail -eq 0 ]
