#!/bin/bash
# CLAUDE.md 수칙 2번: .env, serviceAccount.json, .env.local 커밋 금지
# 또한 .claude/worktrees/ 디렉터리 커밋 금지 (CLAUDE.md 금지사항)

COMMAND=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# .env 관련 파일 git add 차단
if echo "$COMMAND" | grep -qE "git (add|stage).*(\.env|serviceAccount\.json|\.env\.local|lambda_env\.json)"; then
  echo "❌ [block-env-git-add] 민감한 파일의 git add가 차단되었습니다." >&2
  echo "   차단된 파일: .env / serviceAccount.json / .env.local / lambda_env.json" >&2
  echo "   해당 파일들은 .gitignore에 포함되어 있어야 합니다." >&2
  exit 2
fi

# .claude/worktrees/ 커밋 차단
if echo "$COMMAND" | grep -qE "git (add|stage).*\.claude/worktrees"; then
  echo "❌ [block-env-git-add] .claude/worktrees/ 디렉터리는 커밋할 수 없습니다." >&2
  echo "   Claude Code 내부 워크트리 파일입니다. .gitignore에 추가하세요." >&2
  exit 2
fi

exit 0
