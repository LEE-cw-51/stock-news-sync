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

# [Copilot #1] WORKTREE_PATH 디렉터리 존재 여부 검증
if [ ! -d "$WORKTREE_PATH" ]; then
  echo "❌ [setup-worktree-env] 워크트리 경로가 존재하지 않거나 디렉터리가 아닙니다: $WORKTREE_PATH"
  echo "   예: bash .claude/scripts/setup-worktree-env.sh .claude/worktrees/workspace"
  exit 1
fi

# [Copilot #5] WORKTREE_PATH 기준으로 git-common-dir 계산
# → 레포 밖(CWD)에서 실행해도 메인 레포 루트를 정확히 참조
if ! GIT_COMMON_DIR="$(git -C "$WORKTREE_PATH" rev-parse --git-common-dir 2>/dev/null)"; then
  echo "❌ [setup-worktree-env] 지정한 워크트리 경로가 Git 레포지토리가 아닙니다: $WORKTREE_PATH"
  echo "   워크트리 루트 디렉터리를 전달했는지 확인해 주세요."
  exit 1
fi
REPO_ROOT="$(cd "$(git -C "$WORKTREE_PATH" rev-parse --git-common-dir)/.." && pwd)"

link_or_copy() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [ ! -f "$src" ]; then
    echo "⚠️  [$label] 소스 파일 없음: $src (건너뜀)"
    return
  fi

  # [Copilot #2] dst 상위 디렉터리 보장
  mkdir -p "$(dirname "$dst")"

  # [Copilot #3] 심볼릭 링크 존재 시 유효성 검사 (끊어짐 or 잘못된 대상 → 재생성)
  if [ -L "$dst" ]; then
    local current_target
    current_target="$(readlink "$dst" 2>/dev/null || true)"
    if [ "$current_target" = "$src" ] && [ -f "$dst" ]; then
      echo "✅ [$label] 유효한 심볼릭 링크 이미 존재: $dst → $src"
      return
    else
      echo "🔄 [$label] 잘못된/끊어진 링크 감지, 재생성: $dst (기존 대상: $current_target)"
      rm -f "$dst"
    fi
  elif [ -f "$dst" ]; then
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
