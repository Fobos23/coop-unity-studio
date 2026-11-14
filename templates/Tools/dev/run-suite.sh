#!/bin/bash
# Runs autotest scenarios by suite from Tools/dev/autotests.txt, one at a time, and prints one line per scenario.
#   run-suite.sh list                 suites, scenarios and tags
#   run-suite.sh smoke                smoke scenarios of every suite (after every card)
#   run-suite.sh full                 every scenario (stage gate, external build, engine/netcode upgrade, on request)
#   run-suite.sh suite <name>         one whole suite (a smoke failed in a suite the card did not touch)
#   run-suite.sh dry <mode> [name]    print what would run
# Env: RUN_MANUAL=1 also runs scenarios tagged manual (need a human or the internet); RERUN=0 disables the one rerun
# of a failed scenario (a pass on rerun is reported FLAKY); TIMEOUT=<s> default per scenario (tag timeout=<s> wins).
# Exit code 1 if any scenario failed or gave no SUMMARY.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REG="${AUTOTESTS:-$ROOT/Tools/dev/autotests.txt}"
RUNNER="${RUNNER:-$ROOT/Tools/dev/autotest.sh}"
OUT="$ROOT/Builds/autotest"
mode=$1; arg=$2
[ -f "$REG" ] || { echo "no registry $REG" >&2; exit 2; }

rows() { tr -d '\r' < "$REG" | grep -v '^[[:space:]]*#' | awk 'NF >= 2 { tags = (NF >= 3 ? $3 : "-"); print $1, $2, tags }'; }
has() { case ",$1," in *",$2,"*) return 0;; esac; return 1; }
tagval() { echo ",$1," | grep -o ",$2=[^,]*" | head -1 | cut -d= -f2; }

select_rows() {   # $1 mode, $2 suite name
  rows | while read -r suite scen tags; do
    if has "$tags" manual && [ -z "$RUN_MANUAL" ]; then manual=1; else manual=0; fi
    case $1 in
      smoke) has "$tags" smoke && [ $manual = 0 ] && echo "$suite $scen $tags" ;;
      full) [ $manual = 0 ] && echo "$suite $scen $tags" ;;
      suite) [ "$suite" = "$2" ] && [ $manual = 0 ] && echo "$suite $scen $tags" ;;
    esac
  done
}

case $mode in
  list) printf '%-14s %-18s %s\n' suite scenario tags; rows | while read -r a b c; do printf '%-14s %-18s %s\n' "$a" "$b" "$c"; done
        echo; echo "suites without a smoke scenario:"; rows | awk '{ s[$1]=1; if ($3 ~ /(^|,)smoke(,|$)/) k[$1]=1 } END { for (x in s) if (!k[x]) print "  " x }'
        exit 0 ;;
  dry) shift; m=$1; select_rows "$m" "$2" | while read -r a b c; do echo "would run: $b ($a) [$c]"; done; exit 0 ;;
  smoke|full) ;;
  suite) [ -n "$arg" ] || { echo "suite name?" >&2; exit 2; } ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac

list=$(select_rows "$mode" "$arg")
[ -n "$list" ] || { echo "nothing selected for: $mode $arg" >&2; exit 2; }
mkdir -p "$OUT"
n=$(echo "$list" | wc -l); i=0; bad=0; start=$(date +%s)
echo "run-suite $mode $arg: $n scenarios"

# summary <out file> <scenario> -> "pass fail clientfails" or empty
summary() {
  local s; s=$(grep -a -o "SUMMARY $2 pass=[0-9]* fail=[0-9]*" "$1" 2>/dev/null | tail -1)
  [ -n "$s" ] || return
  local p f c
  p=$(echo "$s" | sed 's/.*pass=\([0-9]*\).*/\1/'); f=$(echo "$s" | sed 's/.*fail=\([0-9]*\).*/\1/')
  c=$(awk '/^--- c[0-9]*\.log/{cl=1} /^--- exceptions/{cl=0} cl && /CHECK FAIL/{n++} END{print n+0}' "$1")
  echo "$p $f $c"
}
# failed check names of the host and the clients, comma list
failed_names() {
  { grep -a -o "SUMMARY $2 pass=[0-9]* fail=[0-9]* failed=\[[^]]*\]" "$1" | tail -1 | sed 's/.*failed=\[\(.*\)\]/\1/' | tr -d ' ' | tr ',' '\n'
    awk '/^--- c[0-9]*\.log/{cl=$2} /^--- exceptions/{cl=""} cl && /CHECK FAIL/{ for (i=1;i<=NF;i++) if ($i=="FAIL") { n=$(i+1); sub(/:$/,"",n); print cl ":" n } }' "$1"
  } | grep -v '^$' | head -6 | paste -sd, -
}
human() { local r="$1"; [ -z "$r" ] && { echo "no SUMMARY"; return; }; set -- $r; echo "$1/$(( $1 + $2 )) passed, client fails $3"; }
dur() { [ "$1" -lt 90 ] && echo "${1}s" || echo "$(( ($1 + 30) / 60 )) min"; }

run_one() {   # $1 scenario $2 timeout -> writes $OUT/$1.out; stdin closed so game copies cannot eat the list
  bash "$RUNNER" "$1" "$2" > "$OUT/$1.out" 2>&1 < /dev/null
}

while read -r suite scen tags; do
  i=$((i+1))
  to=$(tagval "$tags" timeout); to=${to:-${TIMEOUT:-600}}
  prev=""; [ -f "$OUT/$scen.out" ] && prev=$(summary "$OUT/$scen.out" "$scen")
  t0=$(date +%s)
  run_one "$scen" "$to"
  res=$(summary "$OUT/$scen.out" "$scen")
  verdict=""
  if [ -z "$res" ] || [ "$(echo $res | cut -d' ' -f2)" != 0 ] || [ "$(echo $res | cut -d' ' -f3)" != 0 ]; then
    first="$res"
    if [ "${RERUN:-1}" = 1 ]; then
      cp "$OUT/$scen.out" "$OUT/$scen.first.out"
      run_one "$scen" "$to"
      res=$(summary "$OUT/$scen.out" "$scen")
      if [ -n "$res" ] && [ "$(echo $res | cut -d' ' -f2)" = 0 ] && [ "$(echo $res | cut -d' ' -f3)" = 0 ]; then
        names=$(failed_names "$OUT/$scen.first.out" "$scen")
        verdict="FLAKY $(human "$res" | cut -d' ' -f1) after rerun (first run: $(human "$first")${names:+: $names}; see $scen.first.out)"
      fi
    fi
  fi
  took=$(dur $(( $(date +%s) - t0 )))
  if [ -z "$verdict" ]; then
    if [ -z "$res" ]; then verdict="NO SUMMARY (GPU hang, port or exception: see $scen.out)"; bad=1
    else
      set -- $res
      total=$(( $1 + $2 ))
      if [ "$2" = 0 ] && [ "$3" = 0 ]; then verdict="PASS $1/$total"
      else verdict="FAIL $2 of $total, client fails $3: $(failed_names "$OUT/$scen.out" "$scen")"; bad=1; fi
      if [ -n "$prev" ]; then
        set -- $prev; ptotal=$(( $1 + $2 ))
        verdict="$verdict (was $1/$ptotal)"
        [ "$total" -lt "$ptotal" ] && { verdict="$verdict FEWER CHECKS: died early?"; bad=1; }
      fi
    fi
  fi
  printf '[%d/%d] %-12s %-16s %s · %s\n' "$i" "$n" "$suite" "$scen" "$verdict" "$took"
done <<< "$list"

echo "total: $(dur $(( $(date +%s) - start ))), $([ $bad = 0 ] && echo green || echo 'FAILURES above')"
echo "logs: $OUT/<scenario>/ and $OUT/<scenario>.out"
exit $bad
