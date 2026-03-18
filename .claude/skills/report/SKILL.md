---
name: report
description: 04번 Tech Lead PM의 표준 보고 형식을 생성합니다. 운영 모드(normal/eco/emergency/handoff)에 맞는 브리핑 템플릿을 채워서 출력합니다.
argument-hint: [mode: normal|eco|emergency|handoff]
allowed-tools: Bash, Read
---

## 04번 표준 보고 형식 생성

### 운영 모드 판단

`$ARGUMENTS`에서 모드를 추출한다. 지정하지 않으면 `normal` 모드로 처리한다.

### 현재 상태 수집

다음을 Read/Bash로 수집하여 맥락을 파악한다:
- `docs/status/PROGRESS.log` 마지막 30줄
- `git log --oneline -5`
- `git status --short`

---

### Normal 모드 출력 (기본값)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[04 Tech Lead PM 보고] — ⚡ 현재 모드: Normal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 진행 상태 및 기계적 검증 결과
  - {PROGRESS.log 기반 최근 완료 작업} — {담당 에이전트}
  - Lint / Test: {/qa 실행 결과 또는 "미실행 — /qa 를 먼저 실행하세요"}
  - 프론트/백엔드 인터페이스: {일치 / 불일치}

■ High Priority (사용자 승인 필요)
  - {없으면 "현재 없음"}

■ 리스크/이슈 및 다음 단계
  - {git log 또는 PROGRESS.log 기반 이슈} — {우선순위} — {대응 방안}

🛑 최종 확인:
검증이 완료되었습니다. 변경 사항을 Commit 및 Merge 할까요? (Y/N)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Eco 모드 출력

Normal 모드에서 각 섹션을 1줄로 압축한다.
상세 설명 없이 핵심 수치와 Pass/Fail만 표시한다.

---

### Emergency 모드 출력

헤더에 `🚨 긴급 대응 중` 추가.
"High Priority" 섹션만 출력하고 나머지 생략.
다음 단계: "긴급 이슈 해결 후 재보고"만 표시.

---

### Handoff 모드 출력

헤더에 `🔄 세션 종료 준비` 추가.
`docs/status/HANDOFF.md` 현재 내용을 Read로 읽어 갱신 체크리스트 출력:

```
[Handoff 체크리스트]
  □ PROGRESS.log 최신 상태로 갱신되었는가?
  □ HANDOFF.md에 완료 작업 요약이 있는가?
  □ HANDOFF.md에 미해결 이슈가 기재되었는가?
  □ HANDOFF.md에 다음 세션 1순위 명령이 있는가?
  □ 02번이 브랜치 merge 후 삭제했는가?

→ /handoff 를 실행하여 HANDOFF.md 갱신 초안을 생성하세요.
```
