#!/bin/bash
# PostToolUse Hook: DB 관련 파일 수정 감지 시 05번 검토 체크리스트 경고
# 차단하지 않고 경고만 출력 (exit 0)

FILE=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

# 감사 대상 파일 목록
DB_FILES=(
  "db_service.py"
  "supabase_schema.sql"
  "market_service.py"
)

MATCHED_FILE=""
for TARGET in "${DB_FILES[@]}"; do
  if [[ "$FILE" == *"$TARGET" ]]; then
    MATCHED_FILE="$TARGET"
    break
  fi
done

if [ -z "$MATCHED_FILE" ]; then
  exit 0
fi

echo "" >&2
echo "⚠️  [warn-db-schema-change] DB 관련 파일 수정이 감지되었습니다." >&2
echo "   파일: $FILE" >&2
echo "" >&2
echo "   체크리스트:" >&2
echo "   [ ] 05번 DB Management Agent 검토 완료?" >&2
echo "   [ ] Firebase 경로 변경 시 frontend/lib/types.ts 동기화?" >&2
echo "   [ ] Supabase DDL 변경 시 04번 승인 후 02번이 실행?" >&2
echo "   [ ] docs/reference/DATA_SCHEMA.md 업데이트 예정?" >&2
echo "" >&2
echo "   DB 감사 실행: /db-audit" >&2

exit 0
