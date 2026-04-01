#!/usr/bin/env bash
# setup-worktree-env.sh
# 워크트리에 env 파일 심볼릭 링크를 생성합니다.
# .env / .env.local 은 gitignore 대상이라 워크트리에 자동 복사되지 않으므로
# 이 스크립트를 /worktree start 직후 실행하여 메인 레포의 파일을 참조합니다.
#
# 사용법:
#   bash .claude/scripts/setup-worktree-env.sh .claude/worktrees/<name>
#
# 동작:
#   1. 심볼릭 링크 생성 시도 (ln -sf)
#   2. 실패 시 (Windows 권한 등) 파일 복사 fallback (cp)

set -e

WORKTREE_PATH="${1:?[setup-worktree-env] 오류: 워크트리 경로를 인수로 전달하세요. 예: bash .claude/scripts/setup-worktree-env.sh .claude/worktrees/workspace}"
REPO_ROOT="$(git rev-parse --show-toplevel)"

link_or_copy() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [ ! -f "$src" ]; then
    echo "⚠️  [$label] 소스 파일 없음: $src (건너뜀)"
    return
  fi

  if [ -L "$dst" ]; then
    echo "✅ [$label] 심볼릭 링크 이미 존재: $dst"
    return
  fi

  if [ -f "$dst" ]; then
    echo "✅ [$label] 파일 이미 존재: $dst"
    return
  fi

  # 심볼릭 링크 시도 → 실패 시 복사 fallback
  if ln -sf "$src" "$dst" 2>/dev/null; then
    echo "🔗 [$label] 심볼릭 링크 생성: $dst → $src"
  elif cp "$src" "$dst"; then
    echo "📋 [$label] 복사 완료 (symlink 실패 fallback): $dst"
  else
    echo "❌ [$label] 링크/복사 모두 실패: $dst"
    return 1
  fi
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[setup-worktree-env] env 파일 셋업"
echo "워크트리: $WORKTREE_PATH"
echo "레포 루트: $REPO_ROOT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

link_or_copy \
  "$REPO_ROOT/backend/.env" \
  "$WORKTREE_PATH/backend/.env" \
  "backend/.env"

link_or_copy \
  "$REPO_ROOT/frontend/.env.local" \
  "$WORKTREE_PATH/frontend/.env.local" \
  "frontend/.env.local"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 완료"
echo ""
