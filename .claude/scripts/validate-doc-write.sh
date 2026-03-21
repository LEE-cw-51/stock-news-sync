#!/bin/bash
# PreToolUse Hook: 04-tech-lead-pm-agent Write/Edit 제한
# 허용 파일: docs/ 하위 모든 .md 파일, docs/status/PROGRESS.log, CLAUDE.md

FILE=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

if [ -z "$FILE" ]; then exit 0; fi

# Windows 경로 구분자 정규화
NORMALIZED=$(echo "$FILE" | tr '\\' '/')

# 허용 패턴:
#   docs/ 하위 모든 .md 파일
#   docs/status/PROGRESS.log
#   루트의 CLAUDE.md
if echo "$NORMALIZED" | grep -qE "(^|/)docs/.*\.md$"; then exit 0; fi
if echo "$NORMALIZED" | grep -qE "(^|/)docs/status/PROGRESS\.log$"; then exit 0; fi
if echo "$NORMALIZED" | grep -qE "(^|/)CLAUDE\.md$"; then exit 0; fi

echo "❌ [validate-doc-write] 04-tech-lead-pm-agent는 문서 파일만 수정 가능합니다." >&2
echo "   차단된 파일: $FILE" >&2
echo "   허용: docs/**/*.md | docs/status/PROGRESS.log | CLAUDE.md" >&2
echo "   소스 코드 수정은 01~03번 에이전트에게 위임하세요." >&2
exit 2
