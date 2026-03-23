#!/bin/bash
# PreToolUse Hook: git commit / git push 전 사용자 승인 확인 경고
# 차단하지 않고 경고만 출력 (exit 0)
# 실제 승인은 Claude가 사용자에게 직접 요청해야 함

COMMAND=$(cat | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if echo "$COMMAND" | grep -qE "git (commit|push)"; then
  echo "" >&2
  echo "⚠️  [warn-before-commit-push] git commit / push 감지" >&2
  echo "   커밋·push 전 반드시 사용자에게 승인을 요청하세요." >&2
  echo "   워크플로우: 코드 변경 → git add → 테스트 결과 보고 → 사용자 승인 → 커밋·push" >&2
  echo "" >&2
fi

exit 0
