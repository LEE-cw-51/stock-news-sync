---
name: setup-env
description: 워크트리 env 파일 셋업. backend/.env + frontend/.env.local 심볼릭 링크(또는 복사)를 생성합니다. /worktree start 이전에 생성된 워크트리나 키 변경 후 재적용 시 사용합니다.
argument-hint: [worktree-path]  — 생략 시 현재 워크트리 자동 감지
allowed-tools: Bash
---

## 워크트리 env 셋업

이 스킬은 **02번(Backend Cloud Agent)만** 실행한다.

`$ARGUMENTS`로 워크트리 경로를 전달하거나, 생략하면 현재 워크트리 루트를 자동 감지한다.

---

### 실행 순서

```bash
# 1. 워크트리 경로 결정
#    - 인자가 있으면 그대로 사용
#    - 없으면 git rev-parse --show-toplevel 로 현재 워크트리 루트 감지
WORKTREE="${ARGUMENTS:-$(git rev-parse --show-toplevel)}"

# 2. 메인 레포 루트 계산 (git-common-dir 경유)
REPO_ROOT="$(cd "$WORKTREE" && cd "$(git rev-parse --git-common-dir)/.." && pwd)"

# 3. setup-worktree-env.sh 실행
bash "$REPO_ROOT/.claude/scripts/setup-worktree-env.sh" "$WORKTREE"
```

---

### 출력 형식

스크립트 출력을 그대로 표시한 뒤, 최종 상태를 한 줄 요약한다:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[setup-env] env 파일 셋업 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
워크트리:            {경로}
backend/.env:        {🔗 심볼릭 링크 생성 | 📋 복사 완료 | ✅ 이미 존재 | ⚠️ 소스 없음}
frontend/.env.local: {동일}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👉 이제 /run-sync 로 테스트를 실행할 수 있습니다.
```

---

### 트리거 상황

- 테스트 실패 메시지에 "API 키" 또는 "환경변수"가 포함된 경우
- `/worktree start` 이전에 생성된 워크트리에서 첫 `/run-sync` 전
- `.env` 키 교체 후 워크트리 재적용이 필요할 때
