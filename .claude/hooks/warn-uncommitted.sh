#!/bin/bash
# Stop Hook: 세션 종료 전 미커밋 변경사항 경고
# 차단하지 않고 경고만 출력 (exit 0)

STATUS=$(git status --short 2>/dev/null)

if [ -n "$STATUS" ]; then
  echo "⚠️  [warn-uncommitted] 커밋되지 않은 변경 사항이 있습니다:" >&2
  echo "$STATUS" | while read -r line; do echo "   $line" >&2; done
  echo "" >&2
  echo "   세션 종료 전 /handoff 스킬을 실행하여 인수인계 문서를 갱신하세요." >&2
  echo "   커밋은 02번 에이전트가 04번 QA 승인 후 수행합니다." >&2
fi

exit 0
