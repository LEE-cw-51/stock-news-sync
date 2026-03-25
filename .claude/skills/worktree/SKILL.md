---
name: worktree
description: 02번 Backend Cloud Agent의 워크트리 및 브랜치 생명주기를 관리합니다. 01번/03번 작업용 브랜치+워크트리 생성(start), 활성 워크트리 목록 조회(list), 병합 완료 브랜치 정리(clean)를 수행합니다.
argument-hint: [start <branch-name> | list | clean]
allowed-tools: Bash
---

## 워크트리 생명주기 관리

`$ARGUMENTS`의 첫 번째 토큰을 서브커맨드로 사용한다.
서브커맨드가 없으면 사용법 안내를 출력한다.

---

### 공통 전제 조건

이 스킬은 **02번(Backend Cloud Agent)만** 실행한다.
01번·03번·04번·05번 에이전트는 이 스킬을 직접 실행하지 않는다.

실행 전 현재 위치가 main 브랜치의 저장소 루트인지 확인한다:
- `git branch --show-current` — `main`이어야 한다
- `git status --short` — 미커밋 변경이 없어야 한다

---

### 서브커맨드: `start <branch-name>`

**목적**: 01번 또는 03번 에이전트가 격리 환경에서 작업할 브랜치와 워크트리를 함께 생성한다.

**`branch-name` 형식**: `/commit-kr` 스킬이 제안한 브랜치명을 그대로 사용한다.
예: `feat/p3-watchlist-ui`, `fix/p3-lambda-timeout`, `docs/agent-directory-update`

**⛔ 사전 승인 필수**: `start`를 실행하기 전에 반드시 사용자에게 생성할 브랜치명과 워크트리명을 제안하고 승인을 받아야 한다. 승인 없이 실행 금지.

**허용 브랜치 접두사**: `feat/`, `fix/`, `hotfix/`, `docs/`, `refactor/`, `chore/`, `test/`, `style/`

**실행 순서**:

```bash
# 1. main 최신화
git fetch origin main

# 2. 이미 존재하는 브랜치인지 확인
git branch --list <branch-name>

# 3. 브랜치 생성 및 워크트리 연결
# 워크트리 경로 = 브랜치명의 슬래시 뒤 마지막 세그먼트
# 예: feat/p3-watchlist-ui → .claude/worktrees/p3-watchlist-ui
git worktree add .claude/worktrees/<last-segment> -b <branch-name>
```

**출력 형식**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[worktree start] 워크트리 생성 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
브랜치:     {branch-name}
워크트리:   .claude/worktrees/{last-segment}
베이스:     main ({최신 커밋 해시 7자리})

01번/03번 에이전트 작업 지시 시:
  → EnterWorktree .claude/worktrees/{last-segment} 로 진입
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 서브커맨드: `list`

**목적**: 현재 활성 워크트리 전체를 조회하고 각 브랜치의 상태를 요약한다.

**실행 순서**:

```bash
git worktree list --porcelain
# 각 브랜치: git log --oneline main..<branch> | wc -l  으로 커밋 수 산출
```

**출력 형식**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[worktree list] 활성 워크트리 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  경로                              브랜치                    커밋(main↑)  마지막 커밋
1  (main)                            main                      —           {메시지}
2  .claude/worktrees/{name}          {branch}                  +{N}커밋     {메시지}

정리 후보 (main과 동일한 브랜치):
  → {branch-name}  (/worktree clean 으로 제거 가능)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 서브커맨드: `clean`

**목적**: main에 이미 병합된 브랜치의 워크트리와 브랜치 레퍼런스를 정리한다.

**실행 순서**:

```bash
# 1. 삭제된 워크트리 레퍼런스 정리
git worktree prune

# 2. 병합 완료 브랜치 목록 미리보기 (삭제 전 확인)
echo "=== 병합 완료 브랜치 (삭제 후보) ==="
git branch --merged main | grep -vE '^\*|\bmain\b'

# 3. claude/ 네임스페이스 브랜치 중 main과 동일한 것 삭제
for b in $(git branch | grep 'claude/' | tr -d ' '); do
  [ $(git log --oneline main..$b | wc -l) -eq 0 ] && git branch -d $b
done

# 4. feat/fix/refactor/docs/hotfix/chore/test/style 브랜치 중 병합 완료된 것 삭제
for b in $(git branch --merged main | grep -E '^\s+(feat|fix|refactor|docs|hotfix|chore|test|style)/' | tr -d ' '); do
  git branch -d $b
done
```

`main`, `HEAD`는 절대 삭제하지 않는다.
병합되지 않은 브랜치(`-d`가 거부하는 경우)는 삭제하지 않으며 목록에 표시한다.

**출력 형식**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[worktree clean] 정리 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
워크트리 prune:    완료
삭제된 브랜치:
  - {branch-name}  (main 병합 완료)
남은 활성 브랜치:
  - {branch-name}  (+{N} 커밋, 작업 중)

⚠️  병합되지 않은 브랜치는 삭제하지 않았습니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 사용 예시 (02번 작업 흐름)

```
# 1. /commit-kr 로 브랜치명 제안 수령
# 2. /worktree start feat/p3-watchlist-ui
# 3. 01번 에이전트에게 워크트리 경로 전달 후 작업 지시
# 4. 작업 완료 → /qa → /commit-kr → 02번 커밋 → main 병합
# 5. /worktree clean  (세션 종료 전 정리)
```

---

### 사용법 출력 (서브커맨드 없음)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[worktree] 사용법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/worktree start <branch-name>   — 브랜치 + 워크트리 생성 (02번 전용)
/worktree list                  — 활성 워크트리 현황 조회
/worktree clean                 — 병합 완료 브랜치/워크트리 정리

브랜치명은 /commit-kr 스킬이 제안한 형식을 사용하세요:
  feat/p{N}-기능명 | fix/p{N}-이슈명 | hotfix/내용 | docs/내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
