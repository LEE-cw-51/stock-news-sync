#!/bin/bash
# CLAUDE.md 수칙 2번: API 키 하드코딩 금지
# 소스 파일에 API 키 패턴이 작성되면 즉시 차단

FILE=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

# 민감한 파일 자체는 검사 제외 (.env, serviceAccount.json은 원래 키가 있음)
if [[ "$FILE" == *".env"* ]] || [[ "$FILE" == *"serviceAccount"* ]] || [[ "$FILE" == *".env.local"* ]]; then
  exit 0
fi

# 파일이 실재하지 않으면 skip
if [ ! -f "$FILE" ]; then
  exit 0
fi

# API 키 패턴 검사 (주석 줄 포함 — 주석에도 실제 키 넣으면 안 됨)
if grep -qE "(gsk_[a-zA-Z0-9]{20,}|AIza[a-zA-Z0-9_\-]{20,}|tvly-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})" "$FILE"; then
  MATCHED=$(grep -nE "(gsk_[a-zA-Z0-9]{20,}|AIza[a-zA-Z0-9_\-]{20,}|tvly-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})" "$FILE" | head -3)
  echo "❌ [block-hardcoded-secrets] API 키 하드코딩이 감지되었습니다!" >&2
  echo "   파일: $FILE" >&2
  echo "   발견된 줄:" >&2
  echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
  echo "   해결: os.environ['KEY_NAME'] 또는 .env 파일을 통해 접근하세요." >&2
  exit 2
fi

exit 0
