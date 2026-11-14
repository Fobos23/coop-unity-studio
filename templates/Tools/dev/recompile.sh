#!/bin/bash
# Refreshes assets in the open editor of this checkout, waits for compilation and prints console errors (exit 1 on errors).
export UNITY_PROJECT_PATH="${UNITY_PROJECT_PATH:-$(cd "$(dirname "$0")/../.." && pwd -W)}"
unity command console clear --no-banner >/dev/null 2>&1
unity command eval --code 'UnityEditor.AssetDatabase.Refresh(); return "ok";' --result-only --no-banner --timeout 120 >/dev/null 2>&1
sleep 8
for i in $(seq 1 50); do
  s=$(unity command recompile_status --result-only --no-banner --timeout 20 2>&1)
  echo "$s" | grep -q '"compiling"\|"triggered"\|timed out\|COMMAND_FAILED\|UNREACHABLE' || break
  sleep 4
done
echo "$s"
# Lines to ignore: known package noise of this project (add with care).
errs=$(unity command console get --level error --tail 30 --result-only --no-banner --timeout 20 2>&1 | grep -o '"message": "[^"]*' | grep -v "invalid signature\|No command named" | tail -30)
if [ -n "$errs" ]; then echo "$errs"; exit 1; fi
echo "no errors"
