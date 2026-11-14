#!/bin/bash
# Autotest scenarios in the built player: autotest.sh <scenario> [timeoutSec]. Logs in Builds/autotest/<scenario>/.
# Registry of suites and smoke: Tools/dev/autotests.txt (run-suite.sh). Contract of the in-game side: Dev/Autotest.cs.
# Env: NOGFX=1 — every copy -batchmode -nographics (GPU hung: logic only, no shots); NETSIM=d,j,loss — client network;
#      NETLOG="<extra args for every copy>" (e.g. -force-d3d12-debug).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
S="$ROOT/Builds/autotest"
EXE="$ROOT/Builds/Windows/__GAME__.exe"
GFX=""; [ -n "$NOGFX" ] && GFX="-batchmode -nographics"
name=$1; to=${2:-600}
D="$S/$name"; rm -rf "$D"; mkdir -p "$D"
W() { cygpath -w "$1"; }
common="-screen-fullscreen 0 -screen-width 640 -screen-height 360 $NETLOG"
big="-screen-fullscreen 0 -screen-width 1280 -screen-height 720 $NETLOG"
# host <players> [scenario] [extra args]; SCEN = the scenario the host runs, passed to clients too (Autotest.cs:
# the scenario body runs on every copy and branches on IsServer; the host's SUMMARY ends the run).
host() { SCEN="${2:-$name}"; "$EXE" $GFX $common -logFile "$(W "$D/host.log")" -profile t_host -autohost -autoplayers "$1" -scenario "$SCEN" $3 >/dev/null 2>&1 & }
# hostbig: the same with 1280x720 and shots (visual checks)
hostbig() { SCEN="${2:-$name}"; "$EXE" $GFX $big -logFile "$(W "$D/host.log")" -profile t_host -autohost -autoplayers "$1" -scenario "$SCEN" -shots "$(W "$D/shots")" $3 >/dev/null 2>&1 & }
# The host's port from its log: a busy 7777 (another copy) moves it to the next free one. A heavy build opens slowly.
hostport() { local i p; for i in $(seq 1 90); do p=$(grep -ao 'host=True port=[0-9]*' "$D/host.log" 2>/dev/null | head -1 | grep -o '[0-9]*$'); [ -n "$p" ] && { echo "$p"; return; }; sleep 1; done; echo 7777; }
# client <id> [extra args]
client() { "$EXE" $GFX $common -logFile "$(W "$D/$1.log")" -profile "t_$1" -autojoin 127.0.0.1 -joinport "$(hostport)" -scenario "${SCEN:-$name}" $2 >/dev/null 2>&1 & }
# Stop only copies of THIS build: other sessions run their own.
stopgame() { powershell.exe -NoProfile -Command "Get-Process __GAME__ -ErrorAction SilentlyContinue | Where-Object { \$_.Path -eq '$(W "$EXE")' } | Stop-Process -Force" >/dev/null 2>&1; }
[ -f "$EXE" ] || { echo "no build: $EXE"; exit 2; }
stopgame
case $name in
  # One player: lobby, session start, the core verb, result, back to the lobby.
  solo) host 1 ;;
  # Host + client: join, the whole flow, both see the same result.
  coop) host 2; sleep 6; client c1 ;;
  # Host quits mid-session: the client gets a clear message and returns to the menu.
  hostleave) host 2; sleep 6; client c1 ;;
  # The flow on a bad network: client -netsim (delay, jitter ms, loss %).
  lanlag) host 2 coop; sleep 6; client c1 "-netsim ${NETSIM:-60,15,2}" ;;
  # Client hits by rewind at ~150 ms (lag compensation on and off compared).
  lagaim) host 2 lagaim; sleep 6; client c1 "-netsim ${NETSIM:-60,10,2}" ;;
  # Max players, max AI: host fps. Clients headless so the PC measures the game, not four windows.
  squadh) host 4 squad; sleep 6; client c1 "-batchmode -nographics -fps 30"; client c2 "-batchmode -nographics -fps 30"; client c3 "-loaddelay 8 -batchmode -nographics -fps 30" ;;
  # Through the internet: the host opens a Relay session and writes the join code to a file, the client joins by it.
  online|onlinelag)
    "$EXE" $GFX $common -logFile "$(W "$D/host.log")" -profile t_host -autohost -autoplayers 2 -scenario coop -online "$(W "$D/code.txt")" >/dev/null 2>&1 &
    sim=""; [ "$name" = onlinelag ] && sim="-netsim ${NETSIM:-60,15,2}"
    sleep 6; "$EXE" $GFX $common -logFile "$(W "$D/c1.log")" -profile t_c1 -joincode "$(W "$D/code.txt")" $sim >/dev/null 2>&1 & ;;
  # Render probe of a map: renderprobe<N> = map/mission N (render.md of the studio skill).
  renderprobe|renderprobe[0-9]*) m=${name#renderprobe}; m=${m:-1}
    "$EXE" $GFX -screen-fullscreen 0 -screen-width 1600 -screen-height 900 $NETLOG -logFile "$(W "$D/host.log")" -profile t_host -autohost -autoplayers 1 -scenario renderprobe -mission $m -shots "$(W "$D/shots")" $PROBEARGS >/dev/null 2>&1 & ;;
  # Add a line per scenario, with a comment saying what it proves, and register it in autotests.txt.
  *) echo "unknown scenario $name"; exit 2 ;;
esac
t=0
stop="SUMMARY|Exception"
while [ $t -lt $to ]; do grep -qaE "$stop" "$D/host.log" 2>/dev/null && break; sleep 5; t=$((t+5)); done
sleep 15
stopgame
echo "=== $name after ${t}s"
grep -ah "CHECK\|SUMMARY\|PERF\|RPROBE\|\[Online\]" "$D/host.log"
for f in "$D"/c*.log; do [ -f "$f" ] && { echo "--- $(basename $f)"; grep -ah "CHECK" "$f"; grep -ah "RESULT\|reconnect\|fps=\|\[Online\]\|NetSim" "$f" | tail -8; }; done
echo "--- exceptions"
grep -ah -A3 "Exception" "$D"/*.log | head -40
