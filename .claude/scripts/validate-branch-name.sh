#!/usr/bin/env bash
# validate-branch-name.sh
# 브랜치명이 프로젝트 네이밍 컨벤션을 따르는지 검증한다.
# 사용법: bash .claude/scripts/validate-branch-name.sh <branch-name>
# 종료 코드: 0 = 유효, 1 = 유효하지 않음

BRANCH="${1:-}"

ALLOWED_PATTERN="^(feat|fix|hotfix|docs|refactor|chore|test|style)/.+"

# claude/ 네임스페이스는 Claude Code 내부 자동 생성 전용 — 검사 제외
CLAUDE_PATTERN="^claude/.+"

if [ -z "$BRANCH" ]; then
  echo "[validate-branch-name] 사용법: bash .claude/scripts/validate-branch-name.sh <branch-name>" >&2
  exit 1
fi

# claude/ 네임스페이스 예외 처리
if echo "$BRANCH" | grep -qE "$CLAUDE_PATTERN"; then
  exit 0
fi

# main, develop 등 보호 브랜치 예외 처리
if echo "$BRANCH" | grep -qE "^(main|develop|HEAD)$"; then
  exit 0
fi

# 컨벤션 검증
if echo "$BRANCH" | grep -qE "$ALLOWED_PATTERN"; then
  exit 0
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "[validate-branch-name] ⚠️  브랜치 네이밍 컨벤션 위반" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "입력한 브랜치명: $BRANCH" >&2
  echo "" >&2
  echo "허용되는 접두사:" >&2
  echo "  feat/     — 새 기능 개발 (예: feat/p4-analytics)" >&2
  echo "  fix/      — 버그 수정   (예: fix/p4-lambda-crash)" >&2
  echo "  hotfix/   — 긴급 수정   (예: hotfix/firebase-auth)" >&2
  echo "  docs/     — 문서 갱신   (예: docs/worktree-guide)" >&2
  echo "  refactor/ — 리팩토링    (예: refactor/p4-ai-service)" >&2
  echo "  chore/    — 빌드/설정   (예: chore/update-deps)" >&2
  echo "  test/     — 테스트 코드 (예: test/p4-market-service)" >&2
  echo "  style/    — 포맷/UI 수정(예: style/dashboard-layout)" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  exit 1
fi
