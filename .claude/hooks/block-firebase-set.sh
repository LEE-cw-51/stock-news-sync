#!/bin/bash
# CLAUDE.md 수칙 4번: db_service.py에서 ref.set() 사용 금지
# ref.set()은 전체 경로를 덮어쓰므로 기존 데이터 손실 위험
# 반드시 ref.update()를 사용해야 함

FILE=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

# db_service.py 파일만 검사
if [[ "$FILE" != *"db_service.py" ]]; then
  exit 0
fi

if [ ! -f "$FILE" ]; then
  exit 0
fi

# ref.set( 패턴 검사 (주석이 아닌 실제 코드 줄만)
if grep -qE "^[^#]*ref\.set\(" "$FILE"; then
  MATCHED=$(grep -nE "^[^#]*ref\.set\(" "$FILE" | head -3)
  echo "❌ [block-firebase-set] db_service.py에서 ref.set() 사용이 감지되었습니다!" >&2
  echo "   파일: $FILE" >&2
  echo "   발견된 줄:" >&2
  echo "$MATCHED" | while read -r line; do echo "     $line" >&2; done
  echo "   해결: ref.set() → ref.update() 로 변경하세요." >&2
  echo "   이유: set()은 해당 경로의 모든 데이터를 덮어씁니다." >&2
  exit 2
fi

exit 0
