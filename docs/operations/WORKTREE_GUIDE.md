# WORKTREE_GUIDE.md — 워크트리 운영 가이드

> 이 문서는 stock-news-sync 프로젝트에서 Git Worktree와 브랜치를 생성·수정·삭제하는 기준과 워크플로우를 정의합니다.
> **담당 에이전트**: 02번(Backend Cloud Agent)

---

## 1. 브랜치 네이밍 컨벤션

모든 브랜치는 아래 접두사로 시작해야 합니다. `validate-branch-name.sh` 훅이 자동으로 검증합니다.

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `feat/` | 새 기능 개발 | `feat/p4-vercel-analytics` |
| `fix/` | 버그 수정 | `fix/p4-lambda-timeout` |
| `hotfix/` | 긴급 수정 (Phase 무관) | `hotfix/firebase-auth` |
| `docs/` | 문서 갱신 | `docs/worktree-guide` |
| `refactor/` | 코드 리팩토링 | `refactor/p4-ai-service` |
| `chore/` | 빌드·설정 변경 | `chore/update-deps` |
| `test/` | 테스트 코드 | `test/p4-market-service` |
| `style/` | 포맷·UI 수정 | `style/dashboard-spacing` |

**예외**:
- `main` — 보호 브랜치, 직접 push 금지
- `claude/` — Claude Code 내부 자동 생성 전용, 수동 생성 금지

---

## 2. 워크트리 경로 규칙

```
워크트리 위치: .claude/worktrees/<브랜치명의 마지막 세그먼트>

예시:
  브랜치: feat/p4-vercel-analytics
  워크트리: .claude/worktrees/p4-vercel-analytics

  브랜치: fix/lambda-crash
  워크트리: .claude/worktrees/lambda-crash
```

---

## 3. 워크트리 생명주기

### 3-1. 생성: `/worktree start`

**실행 전 필수**: 사용자에게 브랜치명과 워크트리명을 제안하고 **승인을 받아야** 합니다.

```bash
# 02번 에이전트가 실행 (승인 후)
/worktree start feat/p4-vercel-analytics
```

생성 후:
- 워크트리 경로: `.claude/worktrees/p4-vercel-analytics`
- 01번/03번 에이전트는 `EnterWorktree .claude/worktrees/p4-vercel-analytics` 로 진입

### 3-2. 확인: `/worktree list`

```bash
/worktree list
```

출력 예시:
```
#  경로                                    브랜치                      커밋(main↑)
1  (main)                                  main                        —
2  .claude/worktrees/p4-vercel-analytics   feat/p4-vercel-analytics    +3커밋
```

### 3-3. 이름 변경: `/rename-worktree`

워크트리 폴더명과 연결된 브랜치명을 함께 변경합니다.

**실행 전 필수**:
1. 사용자 승인
2. 미커밋 변경사항 없음 확인

```bash
# 사용법
/rename-worktree <old-branch-name> <new-branch-name>

# 예시: Claude Code 자동 생성 이름을 컨벤션에 맞게 변경
/rename-worktree claude/sharp-lamport feat/p4-worktree-system
```

내부 동작:
1. 미커밋 변경사항 확인 → 있으면 중단
2. 커밋 해시 기록 (유실 방지)
3. `git branch -m` 으로 브랜치 rename
4. remote 브랜치 존재 시 삭제 후 새 이름으로 push
5. 워크트리 remove → add 로 재연결
6. 커밋 보존 확인

### 3-4. 정리: `/worktree clean`

main에 병합 완료된 브랜치와 워크트리를 정리합니다.

```bash
/worktree clean
```

정리 대상:
- `git branch --merged main` 에 포함된 모든 feature/fix/docs 등 브랜치
- `claude/` 네임스페이스 중 main과 동일한 커밋 브랜치

보호 대상 (절대 삭제 안 함):
- `main`
- `HEAD`
- 미병합 브랜치 (`-d` 거부 시 skip)

---

## 4. 브랜치 유지 기준

| 상태 | 판단 | 조치 |
|------|------|------|
| main에 병합 완료 | 삭제 가능 | `/worktree clean` |
| PR 생성 후 리뷰 대기 중 | 유지 | — |
| 작업 진행 중 (+N 커밋) | 유지 | — |
| 수주 이상 방치, main과 동일 | 삭제 권장 | `/worktree clean` |
| `claude/` 네임스페이스, 병합 완료 | 삭제 | `/worktree clean` |

---

## 5. 표준 워크플로우

```
1. 사용자 요청 접수
       ↓
2. 02번: 브랜치명 제안 (feat/p{N}-기능명)
       ↓
3. ⛔ 사용자 브랜치명 승인
       ↓
4. 02번: /worktree start feat/p{N}-기능명
       ↓
5. 01번/03번: EnterWorktree → 코드 작성
       ↓
6. 04번: /qa 검수 (통과/반려)
       ↓
7. 02번: git add → test_run.py → 결과 보고
       ↓
8. ⛔ 사용자 커밋 승인
       ↓
9. 02번: git commit → git push → gh pr create
       ↓
10. ⛔ 사용자 GitHub에서 PR merge
       ↓
11. 02번: /worktree clean
```

---

## 6. 이름 변경이 필요한 경우

Claude Code가 자동으로 생성한 `claude/sharp-lamport` 같은 브랜치명을 컨벤션에 맞게 변경해야 할 때:

```bash
# 1. 현재 상태 확인
/worktree list

# 2. 이름 변경 (사용자 승인 후)
/rename-worktree claude/sharp-lamport feat/p4-worktree-system

# 3. 새 워크트리로 재진입
EnterWorktree .claude/worktrees/p4-worktree-system
```

---

## 7. 관련 파일

| 파일 | 역할 |
|------|------|
| `.claude/skills/worktree/SKILL.md` | start/list/clean 서브커맨드 정의 |
| `.claude/skills/rename-worktree/SKILL.md` | 이름 변경 스킬 정의 |
| `.claude/scripts/rename-worktree.sh` | rename 실행 스크립트 |
| `.claude/scripts/validate-branch-name.sh` | 브랜치명 컨벤션 검증 스크립트 |
| `.claude/hooks/validate-branch-name-hook.sh` | PreToolUse 훅 (브랜치 생성 감지) |
| `.claude/settings.json` | 훅 등록 설정 |
| `.claude/agents/02_backend_cloud_agent.md` | 02번 에이전트 규칙 (승인 절차 포함) |
