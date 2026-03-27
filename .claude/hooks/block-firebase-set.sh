#!/bin/bash
# CLAUDE.md 수칙 4번: db_service.py에서 ref.set() 사용 금지
# Write/Edit 도구 실행 전(PreToolUse) 새 내용에서 직접 검사
# ref.set()은 전체 경로를 덮어쓰므로 기존 데이터 손실 위험 — 반드시 ref.update() 사용

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# db_service.py 파일만 검사
if [[ "$FILE" != *"db_service.py" ]]; then
  exit 0
fi

# Write 도구: tool_input.content에서 직접 검사
if [[ "$TOOL_NAME" == "Write" ]]; then
  CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('content',''))" 2>/dev/null || echo "")
  if echo "$CONTENT" | grep -qE "^[^#]*ref\.set\("; then
    MATCHED=$(echo "$CONTENT" | grep -nE "^[^#]*ref\.set\(" | head -3)
    echo "❌ [block-firebase-set] db_service.py에서 ref.set() 사용이 감지되었습니다! (Write)" >&2
    echo "   파일: $FILE" >&2
    echo "   발견된 줄:" >&2
    echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
    echo "   해결: ref.set() → ref.update() 로 변경하세요." >&2
    echo "   이유: set()은 해당 경로의 모든 데이터를 덮어씁니다." >&2
    exit 2
  fi
  exit 0
fi

# Edit 도구: tool_input.new_string에서 직접 검사
if [[ "$TOOL_NAME" == "Edit" ]]; then
  NEW_STRING=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('new_string',''))" 2>/dev/null || echo "")
  if echo "$NEW_STRING" | grep -qE "^[^#]*ref\.set\("; then
    MATCHED=$(echo "$NEW_STRING" | grep -nE "^[^#]*ref\.set\(" | head -3)
    echo "❌ [block-firebase-set] db_service.py에서 ref.set() 사용이 감지되었습니다! (Edit)" >&2
    echo "   파일: $FILE" >&2
    echo "   발견된 줄:" >&2
    echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
    echo "   해결: ref.set() → ref.update() 로 변경하세요." >&2
    echo "   이유: set()은 해당 경로의 모든 데이터를 덮어씁니다." >&2
    exit 2
  fi
  exit 0
fi

exit 0
