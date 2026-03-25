#!/bin/bash
# PreToolUse Hook: 브랜치 생성 명령 감지 시 네이밍 컨벤션 검증
# git checkout -b <branch> 또는 git branch <branch> 또는 git worktree add ... -b <branch> 패턴 감지
# 컨벤션 위반 시 경고를 출력하되 차단하지 않음 (exit 0)

COMMAND=$(cat | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# 브랜치 생성 패턴 감지
# git checkout -b <branch> / git switch -c <branch> / git branch <branch> / git worktree add ... -b <branch>
BRANCH_NAME=""

if echo "$COMMAND" | grep -qE "git checkout -b |git switch -c "; then
  BRANCH_NAME=$(echo "$COMMAND" | grep -oE "(checkout -b|switch -c) [^ ]+" | awk '{print $NF}')
elif echo "$COMMAND" | grep -qE "git worktree add .+ -b "; then
  BRANCH_NAME=$(echo "$COMMAND" | grep -oE "\-b [^ ]+" | awk '{print $2}')
elif echo "$COMMAND" | grep -qE "git branch [^-]"; then
  # git branch <name> (새 브랜치 생성, -d/-m/-a 등 옵션 제외)
  BRANCH_NAME=$(echo "$COMMAND" | grep -oE "git branch [a-zA-Z][^ ]+" | awk '{print $3}')
fi

if [ -n "$BRANCH_NAME" ]; then
  # validate-branch-name.sh 호출
  SCRIPT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/.claude/scripts"
  if [ -f "$SCRIPT_DIR/validate-branch-name.sh" ]; then
    bash "$SCRIPT_DIR/validate-branch-name.sh" "$BRANCH_NAME" 2>&1 || true
  fi
fi

exit 0
