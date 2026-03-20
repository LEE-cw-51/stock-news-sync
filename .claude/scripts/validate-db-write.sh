#!/bin/bash
# PreToolUse Hook: 05-db-management-agent Write/Edit 제한
# 허용 파일: supabase_schema.sql, DATA_SCHEMA.md

FILE=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

if [ -z "$FILE" ]; then exit 0; fi

# Windows 경로 구분자 정규화
NORMALIZED=$(echo "$FILE" | tr '\\' '/')

if echo "$NORMALIZED" | grep -qE "(backend/db/supabase_schema\.sql|docs/reference/DATA_SCHEMA\.md)$"; then
  exit 0
fi

echo "❌ [validate-db-write] 05-db-management-agent는 지정 파일만 수정 가능합니다." >&2
echo "   차단된 파일: $FILE" >&2
echo "   허용: backend/db/supabase_schema.sql | docs/reference/DATA_SCHEMA.md" >&2
exit 2
