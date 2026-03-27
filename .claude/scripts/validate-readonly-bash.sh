#!/bin/bash
# PreToolUse Hook: 04-tech-lead-pm-agent Bash 제한
# 허용: git status/log/diff, npm run lint/build

COMMAND=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then exit 0; fi

# 읽기 전용 git
if echo "$COMMAND" | grep -qE "^[[:space:]]*git[[:space:]]+(status|log|diff)(\s|$)"; then exit 0; fi
# npm lint/build
if echo "$COMMAND" | grep -qE "^[[:space:]]*npm[[:space:]]+run[[:space:]]+(lint|build)(\s|$)"; then exit 0; fi

echo "❌ [validate-readonly-bash] 04-tech-lead-pm-agent 허용 명령 초과입니다." >&2
echo "   차단된 명령: $COMMAND" >&2
echo "   허용: git status/log/diff | npm run lint/build" >&2
echo "   커밋은 02번(Backend Cloud) 에이전트에게 위임하세요." >&2
exit 2
