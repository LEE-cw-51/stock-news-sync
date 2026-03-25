#!/usr/bin/env bash
# rename-worktree.sh
# 워크트리와 연결된 브랜치명을 안전하게 변경하고 Git과 동기화한다.
# 사용법: bash .claude/scripts/rename-worktree.sh <old-branch> <new-branch>

set -euo pipefail

OLD_BRANCH="${1:-}"
NEW_BRANCH="${2:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

abort() {
  echo -e "${RED}[rename-worktree] ❌ 중단: $1${NC}" >&2
  exit 1
}

info() {
  echo -e "${YELLOW}[rename-worktree] → $1${NC}"
}

ok() {
  echo -e "${GREEN}[rename-worktree] ✅ $1${NC}"
}

# ─── 사용법 출력 ────────────────────────────────────────────
if [ -z "$OLD_BRANCH" ] || [ -z "$NEW_BRANCH" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "[rename-worktree] 사용법"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "bash .claude/scripts/rename-worktree.sh <old-branch> <new-branch>"
  echo ""
  echo "예시:"
  echo "  bash .claude/scripts/rename-worktree.sh claude/sharp-lamport feat/p4-worktree-system"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi

# ─── Step 1: 입력값 검증 ────────────────────────────────────
info "Step 1: 입력값 검증 중..."

# old-branch 존재 확인
if ! git branch --list "$OLD_BRANCH" | grep -q .; then
  abort "브랜치 '$OLD_BRANCH'가 존재하지 않습니다."
fi

# new-branch 네이밍 컨벤션 검증
ALLOWED_PATTERN="^(feat|fix|hotfix|docs|refactor|chore|test|style)/.+"
if ! echo "$NEW_BRANCH" | grep -qE "$ALLOWED_PATTERN"; then
  abort "브랜치명 '$NEW_BRANCH'이 컨벤션을 따르지 않습니다.
허용 접두사: feat/ fix/ hotfix/ docs/ refactor/ chore/ test/ style/"
fi

# new-branch 중복 확인
if git branch --list "$NEW_BRANCH" | grep -q .; then
  abort "브랜치 '$NEW_BRANCH'가 이미 존재합니다. 다른 이름을 사용하세요."
fi

ok "입력값 검증 완료"

# ─── Step 2: 미커밋 변경사항 확인 ──────────────────────────
info "Step 2: 대상 워크트리 미커밋 변경사항 확인 중..."

# old-branch가 연결된 워크트리 경로 찾기
WORKTREE_PATH=$(git worktree list --porcelain | awk '
  /^worktree / { path = $2 }
  /^branch refs\/heads\// { branch = substr($2, 18) }
  /^$/ { if (branch == "'"$OLD_BRANCH"'") print path }
')

if [ -z "$WORKTREE_PATH" ]; then
  # 워크트리가 없으면 현재 브랜치인지 확인
  CURRENT=$(git branch --show-current)
  if [ "$CURRENT" = "$OLD_BRANCH" ]; then
    WORKTREE_PATH="$(pwd)"
  else
    # 워크트리 없이 브랜치만 존재하는 경우 — Step 6 재연결 불필요
    WORKTREE_PATH=""
  fi
fi

if [ -n "$WORKTREE_PATH" ] && [ -d "$WORKTREE_PATH" ]; then
  DIRTY=$(git -C "$WORKTREE_PATH" status --short 2>/dev/null || true)
  if [ -n "$DIRTY" ]; then
    abort "워크트리 '$WORKTREE_PATH'에 미커밋 변경사항이 있습니다.
먼저 커밋하거나 stash한 후 다시 실행하세요:
  git -C \"$WORKTREE_PATH\" status"
  fi
fi

ok "미커밋 변경사항 없음 확인"

# ─── Step 3: 현재 커밋 해시 기록 ───────────────────────────
info "Step 3: 커밋 해시 기록 중..."
COMMIT_HASH=$(git rev-parse "$OLD_BRANCH")
COMMIT_SHORT="${COMMIT_HASH:0:7}"
ok "보존할 커밋: $COMMIT_SHORT"

# ─── Step 4: 브랜치명 변경 ─────────────────────────────────
info "Step 4: 브랜치명 변경 중... ($OLD_BRANCH → $NEW_BRANCH)"
git branch -m "$OLD_BRANCH" "$NEW_BRANCH"
ok "브랜치 rename 완료 (로컬 커밋 히스토리 유지됨)"

# ─── Step 5: remote 브랜치 처리 ────────────────────────────
info "Step 5: remote 브랜치 확인 중..."
if git ls-remote --heads origin "$OLD_BRANCH" 2>/dev/null | grep -q .; then
  info "remote 브랜치 '$OLD_BRANCH' 발견 → 삭제 후 새 이름으로 push"
  git push origin --delete "$OLD_BRANCH" || echo -e "${YELLOW}  ⚠️  remote 삭제 실패 (권한 확인 필요)${NC}"
  git push -u origin "$NEW_BRANCH" || echo -e "${YELLOW}  ⚠️  remote push 실패 (수동 push 필요: git push -u origin $NEW_BRANCH)${NC}"
  ok "remote 브랜치 처리 완료"
else
  info "remote 브랜치 없음 — 로컬 rename만 수행"
fi

# ─── Step 6: 워크트리 재연결 ────────────────────────────────
NEW_SEG="${NEW_BRANCH##*/}"
NEW_WORKTREE_PATH=".claude/worktrees/$NEW_SEG"

if [ -n "$WORKTREE_PATH" ] && [ -d "$WORKTREE_PATH" ] && [ "$WORKTREE_PATH" != "$(pwd)" ]; then
  info "Step 6: 워크트리 재연결 중..."
  OLD_SEG="${OLD_BRANCH##*/}"

  git worktree remove --force "$WORKTREE_PATH"
  git worktree add "$NEW_WORKTREE_PATH" "$NEW_BRANCH"

  # 커밋 보존 확인
  ACTUAL_HASH=$(git -C "$NEW_WORKTREE_PATH" rev-parse HEAD 2>/dev/null | cut -c1-7 || echo "unknown")
  if [ "$ACTUAL_HASH" = "$COMMIT_SHORT" ]; then
    ok "워크트리 재연결 완료 (커밋 보존 확인: $ACTUAL_HASH)"
  else
    echo -e "${YELLOW}[rename-worktree] ⚠️  커밋 해시 불일치 (예상: $COMMIT_SHORT, 실제: $ACTUAL_HASH)${NC}"
  fi
else
  info "Step 6: 독립 워크트리 없음 — 재연결 불필요"
  NEW_WORKTREE_PATH="(워크트리 없음)"
fi

# ─── Step 7: 결과 출력 ──────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[rename-worktree] 변경 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "브랜치:     $OLD_BRANCH → $NEW_BRANCH"
if [ "$WORKTREE_PATH" != "" ] && [ "$NEW_WORKTREE_PATH" != "(워크트리 없음)" ]; then
  echo "워크트리:   $WORKTREE_PATH → $NEW_WORKTREE_PATH"
  echo ""
  echo "다음 단계:"
  echo "  → EnterWorktree $NEW_WORKTREE_PATH 로 재진입"
fi
echo "커밋 보존:  $COMMIT_SHORT ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
