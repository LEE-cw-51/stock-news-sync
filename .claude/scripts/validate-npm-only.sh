#!/bin/bash
# PreToolUse Hook: 01-frontend-agent Bash 제한
# npm/npx 명령만 허용

COMMAND=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then exit 0; fi

if echo "$COMMAND" | grep -qE "^[[:space:]]*(npm|npx)[[:space:]]"; then
  exit 0
fi

# 워크트리 상태 파악용 git 읽기 전용 명령 허용
if echo "$COMMAND" | grep -qE "^[[:space:]]*git[[:space:]]+(status|diff|log)(\s|$)"; then
  exit 0
fi

echo "❌ [validate-npm-only] 01-frontend-agent은 npm/npx 및 git 읽기 명령만 허용합니다." >&2
echo "   차단된 명령: $COMMAND" >&2
echo "   git 쓰기 작업은 02번(Backend Cloud)에게 위임하세요." >&2
exit 2
