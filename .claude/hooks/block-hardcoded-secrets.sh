#!/bin/bash
# CLAUDE.md 수칙 2번: API 키 하드코딩 금지
# Write/Edit 도구 실행 전(PreToolUse) 새 내용에서 직접 검사

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# 민감한 파일 자체는 검사 제외 (.env, serviceAccount.json은 원래 키가 있음)
if [[ "$FILE" == *".env"* ]] || [[ "$FILE" == *"serviceAccount"* ]] || [[ "$FILE" == *".env.local"* ]]; then
  exit 0
fi

SECRET_PATTERN="(gsk_[a-zA-Z0-9]{20,}|AIza[a-zA-Z0-9_\-]{20,}|tvly-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})"

# Write 도구: tool_input.content에서 직접 검사
if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('content',''))" 2>/dev/null || echo "")
  if echo "$CONTENT" | grep -qE "$SECRET_PATTERN"; then
    MATCHED=$(echo "$CONTENT" | grep -nE "$SECRET_PATTERN" | head -3)
    echo "❌ [block-hardcoded-secrets] API 키 하드코딩이 감지되었습니다! (Write)" >&2
    echo "   파일: $FILE" >&2
    echo "   발견된 줄:" >&2
    echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
    echo "   해결: os.environ['KEY_NAME'] 또는 .env 파일을 통해 접근하세요." >&2
    exit 2
  fi
  exit 0
fi

# Edit 도구: tool_input.new_string에서 직접 검사
if [[ "$TOOL_NAME" == "Edit" ]]; then
  NEW_STRING=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('new_string',''))" 2>/dev/null || echo "")
  if echo "$NEW_STRING" | grep -qE "$SECRET_PATTERN"; then
    MATCHED=$(echo "$NEW_STRING" | grep -nE "$SECRET_PATTERN" | head -3)
    echo "❌ [block-hardcoded-secrets] API 키 하드코딩이 감지되었습니다! (Edit)" >&2
    echo "   파일: $FILE" >&2
    echo "   발견된 줄:" >&2
    echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
    echo "   해결: os.environ['KEY_NAME'] 또는 .env 파일을 통해 접근하세요." >&2
    exit 2
  fi
  exit 0
fi

exit 0
