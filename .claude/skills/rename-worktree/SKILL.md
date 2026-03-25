---
name: rename-worktree
description: 현재 워크트리와 연결된 브랜치명·폴더명을 안전하게 변경하고 Git과 동기화합니다. 미커밋 변경사항 체크, 브랜치 rename, 워크트리 재연결, 로컬 커밋 보존을 모두 수행합니다.
argument-hint: <old-branch-name> <new-branch-name>
allowed-tools: Bash
---

## 워크트리 + 브랜치 안전 rename

`$ARGUMENTS`에서 `<old-branch-name>`과 `<new-branch-name>`을 파싱한다.
인자가 부족하면 사용법 안내를 출력한다.

---

### 전제 조건

이 스킬은 **02번(Backend Cloud Agent)만** 실행한다.

실행 전 반드시 확인:
1. **사용자 승인**: 변경할 브랜치명과 새 이름을 사용자에게 먼저 확인받는다.
2. **미커밋 변경 없음**: 대상 워크트리에 미커밋 변경사항이 있으면 실행 중단.
3. **새 브랜치명 컨벤션**: `feat/`, `fix/`, `hotfix/`, `docs/`, `refactor/`, `chore/`, `test/`, `style/` 중 하나로 시작해야 한다.

---

### 실행 스크립트

```bash
bash .claude/scripts/rename-worktree.sh <old-branch-name> <new-branch-name>
```

스크립트가 모든 단계를 처리한다. 직접 git 명령을 조각 실행하지 않는다.

---

### 스크립트 내부 동작 (rename-worktree.sh)

```
Step 1: 입력값 검증
  - old-branch 존재 확인 (git branch --list)
  - new-branch 네이밍 컨벤션 검증 (validate-branch-name.sh 호출)
  - new-branch 중복 확인

Step 2: 대상 워크트리의 미커밋 변경사항 확인
  - git worktree list --porcelain 으로 워크트리 경로 특정
  - 해당 워크트리 디렉터리에서 git status --short 실행
  - 변경사항 있으면 abort (데이터 유실 방지)

Step 3: 현재 커밋 해시 기록 (안전장치)
  - git rev-parse <old-branch> 로 최신 커밋 저장

Step 4: 브랜치명 변경
  - git branch -m <old-branch> <new-branch>
  - (로컬 커밋 히스토리 유지됨 — 브랜치 포인터만 이동)

Step 5: remote 브랜치 처리 (존재하는 경우만)
  - git ls-remote --heads origin <old-branch> 로 remote 존재 확인
  - 있으면: git push origin --delete <old-branch>
  - 있으면: git push -u origin <new-branch>

Step 6: 워크트리 재연결
  - git worktree remove --force <old-worktree-path>
  - 새 경로(브랜치명의 마지막 세그먼트): git worktree add <new-worktree-path> <new-branch>
  - 재연결 후 git log -1 로 커밋 보존 확인

Step 7: 결과 출력
```

---

### 출력 형식

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[rename-worktree] 변경 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
브랜치:     {old-branch} → {new-branch}
워크트리:   .claude/worktrees/{old-seg} → .claude/worktrees/{new-seg}
커밋 보존:  {커밋 해시 7자리} ✅

다음 단계:
  → EnterWorktree .claude/worktrees/{new-seg} 로 재진입
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 오류 케이스

| 상황 | 동작 |
|------|------|
| 미커밋 변경사항 있음 | 즉시 abort, 먼저 커밋 또는 stash 안내 |
| new-branch 네이밍 오류 | abort, 허용 패턴 안내 |
| new-branch 이미 존재 | abort, 다른 이름 제안 요청 |
| remote push 실패 | 로컬 rename은 유지, 사용자에게 수동 push 안내 |

---

### 사용법 출력 (인자 없음)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[rename-worktree] 사용법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/rename-worktree <old-branch-name> <new-branch-name>

예시:
  /rename-worktree claude/sharp-lamport feat/p4-worktree-system
  /rename-worktree fix/p3-old-name fix/p4-correct-name

주의:
  - 미커밋 변경사항이 없는 상태에서만 실행 가능
  - new-branch-name은 feat/fix/hotfix/docs/refactor/chore/test/style 로 시작해야 함
  - 실행 전 사용자 승인 필수
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
