---
name: handoff
description: 세션 종료 시 docs/status/HANDOFF.md 갱신 초안을 생성하고 인수인계 체크리스트를 출력합니다. 04번 Handoff 모드 프로세스를 단계별로 안내합니다.
argument-hint: [completed: 완료작업] [blocker: 미해결이슈] [next: 다음세션명령]
allowed-tools: Bash, Read
---

## 세션 인수인계 실행

**이 스킬은 파일을 직접 수정하지 않는다.**
HANDOFF.md 갱신 초안을 출력하면 04번(또는 02번)이 실제 파일에 적용한다.

---

### STEP 1 — 현재 상태 수집

다음을 실행한다:
- `git log --oneline -5` — 최근 커밋
- `git status --short` — 미커밋 변경사항
- `git branch --show-current` — 현재 브랜치
- `docs/status/PROGRESS.log` 마지막 20줄 Read
- `docs/status/HANDOFF.md` 현재 내용 Read

---

### STEP 2 — 미커밋 경고

`git status`에 미커밋 파일이 있으면 출력:

```
⚠️ 아직 커밋되지 않은 변경 파일이 있습니다:
  {파일 목록}

Handoff 전에 02번을 통해 커밋하거나, 다음 세션으로 이월할 작업임을 명시하세요.
```

---

### STEP 3 — HANDOFF.md 갱신 초안 생성

`$ARGUMENTS`에서 완료 작업, 미해결 이슈, 다음 명령을 추출한다.
인수가 없으면 PROGRESS.log와 git log를 기반으로 자동 추론한다.

출력 형식:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[handoff] docs/status/HANDOFF.md 갱신 초안
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

아래 내용을 docs/status/HANDOFF.md에 기록해 주세요:

[SESSION_HANDOFF_DATA]
- Date: {오늘 날짜 YYYY-MM-DD}
- Last Active Agent: {현재 작업 에이전트}
- Completed:
  1. {완료 작업 1}
  2. {완료 작업 2}
  3. {완료 작업 3 (없으면 생략)}
- Blocker/Issue: {미해결 이슈 또는 "없음"}
- Next Action: {다음 세션 1순위 실행 명령}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 4 — 세션 종료 체크리스트

```
[세션 종료 체크리스트]

02번(Backend Cloud) 확인:
  □ 작업 브랜치가 main에 merge되었는가?
  □ 작업 브랜치가 삭제되었는가? (git branch -d)
  □ git worktree prune 실행했는가?
  □ claude/* 브랜치 중 main과 동일한 것 삭제했는가?

04번(Tech Lead PM) 확인:
  □ PROGRESS.log가 갱신되었는가?
  □ 위 HANDOFF.md 초안이 파일에 적용되었는가?
  □ ROADMAP.md Phase 진행 상황이 업데이트되었는가?

완료 후: "새로운 세션(claude 재실행)을 시작해 주세요"
```

---

### STEP 5 — Handoff 보고 출력

마지막으로 `/report handoff` 형식의 보고를 출력한다.

---

### 권장 실행 순서

```
/qa → 확인 → /commit-kr → 02번 커밋 → /report handoff → /handoff → claude 재시작
```
