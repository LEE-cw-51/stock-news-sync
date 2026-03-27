#!/bin/bash
# CLAUDE.md 수칙 3번: aws lambda update-function-code 직접 실행 금지
# 배포는 반드시 브랜치 push → PR → 사용자 merge → GitHub Actions 경유

COMMAND=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if echo "$COMMAND" | grep -qE "aws lambda (update-function-code|create-function|update-function-configuration)"; then
  echo "❌ [block-direct-lambda] 직접 Lambda 배포는 금지됩니다." >&2
  echo "   배포 순서: 브랜치 push → PR 생성 → 사용자 merge → GitHub Actions → S3 → Lambda" >&2
  echo "   수동 배포가 필요한 경우 사용자(04번)에게 승인 요청하세요." >&2
  exit 2
fi

exit 0
