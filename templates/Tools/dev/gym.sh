#!/bin/bash
# Starts a gym of the built game for the director to play: gym.sh <GymName> [--coop] [--netsim d,j,loss]
#   alone:    one window, host, the gym scene loaded directly (-gym <GymName>)
#   --coop:   plus a client window on this PC with -netsim (default 60,10,2: ~150 ms, 2 % loss) — judge feel as a
#             client sees it; a friend can join over Relay instead.
# Logs in Builds/gyms/<GymName>/; "[GYM] saved …" lines carry the tuned values.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXE="$ROOT/Builds/Windows/__GAME__.exe"
name=$1; shift || true
[ -n "$name" ] || { sed -n '2,6p' "$0"; exit 2; }
coop=""; sim="60,10,2"
while [ $# -gt 0 ]; do
  case $1 in
    --coop) coop=1; shift ;;
    --netsim) sim=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
[ -f "$EXE" ] || { echo "no build: $EXE"; exit 2; }
D="$ROOT/Builds/gyms/$name"; mkdir -p "$D"
W() { cygpath -w "$1"; }
win="-screen-fullscreen 0 -screen-width 1280 -screen-height 720"
"$EXE" $win -logFile "$(W "$D/host.log")" -profile g_host -autohost -autoplayers 1 -gym "$name" >/dev/null 2>&1 &
echo "host: $D/host.log"
if [ -n "$coop" ]; then
  port=7777
  for i in $(seq 1 90); do p=$(grep -ao 'host=True port=[0-9]*' "$D/host.log" 2>/dev/null | head -1 | grep -o '[0-9]*$'); [ -n "$p" ] && { port=$p; break; }; sleep 1; done
  "$EXE" $win -logFile "$(W "$D/c1.log")" -profile g_c1 -autojoin 127.0.0.1 -joinport "$port" -gym "$name" -netsim "$sim" >/dev/null 2>&1 &
  echo "client (-netsim $sim): $D/c1.log"
fi
