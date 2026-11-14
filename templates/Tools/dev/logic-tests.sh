#!/bin/bash
# Logic tests (__NS__.Dev.LogicTests.Run) in the open editor of this checkout. Right after the editor opens use a longer
# timeout: LOGIC_TIMEOUT=500 bash Tools/dev/logic-tests.sh
export UNITY_PROJECT_PATH="${UNITY_PROJECT_PATH:-$(cd "$(dirname "$0")/../.." && pwd -W)}"
out=$(unity command eval --code 'return __NS__.Dev.LogicTests.Run();' --result-only --no-banner --timeout "${LOGIC_TIMEOUT:-120}" 2>&1)
echo "$out" | sed 's/\\n/\n/g'
echo "$out" | grep -q "fail=0" || exit 1
