---
name: commit-kr
description: 변경된 파일을 분석하여 프로젝트 한국어 커밋 컨벤션에 맞는 커밋 메시지와 브랜치명을 제안합니다. 실제 커밋은 수행하지 않으며 02번 에이전트에게 전달할 초안을 출력합니다.
argument-hint: [작업 내용 간략 설명 (선택)]
allowed-tools: Bash, Read
---

## 한국어 커밋 메시지 초안 생성

### 현재 변경 상태 파악

`git diff --name-status HEAD`와 `git status --short`를 실행하여
변경된 파일 목록과 변경 유형을 확인한다.

`$ARGUMENTS`로 작업 내용 힌트가 제공된 경우 참고한다.

---

### 태그 선택 기준

| 태그 | 선택 기준 |
|------|----------|
| `[Feat]` | 새 기능/컴포넌트/서비스 함수 추가 |
| `[Fix]` | 버그 수정, 오류 처리 보완, cleanup 누락 추가 |
| `[Docs]` | `.md` 파일만 변경, CLAUDE.md/PROGRESS.log 갱신 |
| `[Style]` | CSS/Tailwind 변경, 포맷팅, UI 조정 (로직 변경 없음) |
| `[Refactor]` | 기존 기능 유지하며 코드 구조 개선 |
| `[Test]` | `test_run.py` 수정, 테스트 케이스 추가 |
| `[Chore]` | `requirements.txt`, `package.json` 변경, CI/CD 수정 |

---

### 브랜치명 제안

`docs/status/ROADMAP.md`를 Read로 읽어 현재 Phase 번호를 추론한 후 브랜치명을 제안한다.

형식: `{유형}/p{N}-{기능명-kebab-case}`

| 유형 | 형식 | 예시 |
|------|------|------|
| 기능 | `feat/p{N}-기능명` | `feat/p3-watchlist-ui` |
| 버그 | `fix/p{N}-이슈명` | `fix/p3-lambda-timeout` |
| 핫픽스 | `hotfix/내용` | `hotfix/firebase-auth` |
| 문서 | `docs/내용` | `docs/handoff-update` |

---

### 출력 형식

**실제 git commit은 절대 실행하지 않는다.**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[commit-kr] 02번 에이전트 커밋 요청 초안
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
변경 파일:
  {git status 출력}

추천 커밋 메시지:
  [태그]: 작업 내용 (한글, 명사형 또는 동사형 종결)

대안 메시지:
  [태그]: 대안 설명 (태그가 애매한 경우)

추천 브랜치명: {유형}/p{N}-{기능명}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  커밋 금지 사항 확인:
  - /qa 실행 → 전체 통과 후 진행
  - 01번·03번은 직접 커밋 불가 → 이 초안을 02번에 전달
  - 02번이 04번 QA 승인 후 실제 커밋·병합 수행
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
