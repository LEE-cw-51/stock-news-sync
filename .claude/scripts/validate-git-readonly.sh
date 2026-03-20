#!/bin/bash
# PreToolUse Hook: 05-db-management-agent Bash 제한
# git log/diff/status 만 허용

COMMAND=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then exit 0; fi

if echo "$COMMAND" | grep -qE "^[[:space:]]*git[[:space:]]+(log|diff|status)(\s|$)"; then
  exit 0
fi

echo "❌ [validate-git-readonly] 05-db-management-agent의 Bash는 git log/diff/status만 허용합니다." >&2
echo "   차단된 명령: $COMMAND" >&2
echo "   DB 에이전트는 설계·감사·문서화만 수행합니다." >&2
exit 2
