# 협업 플레이북 (Standard Operating Procedures)

> 관리 주체: **04번 Tech Lead PM**
> 최종 수정: 2026-02-27

---

## 개요

이 문서는 stock-news-sync 프로젝트의 표준 협업 프로세스(SOP)를 정의한다.
모든 에이전트는 이 플레이북에 따라 작업하고 보고한다.

**핵심 원칙**: 01~03번 에이전트는 사용자에게 직접 보고하지 않는다.
모든 보고는 04번(Tech Lead PM)을 경유하며, 04번이 우선순위를 선정하여 최종 브리핑한다.

---

## SOP 1: 일반 개발 흐름

일상적인 기능 개발, 버그 수정, 리팩토링 작업에 적용한다.

```
Step 1. 사용자 요청 접수
    │   사용자가 작업을 지시한다.
    ↓
Step 2. 04번 Tech Lead PM — 작업 분배
    │   요청을 분석하여 적절한 에이전트에게 할당한다.
    │   ├── UI/UX·디자인 개편 → 01번 (Frontend)
    │   ├── 백엔드 로직·인프라 → 02번 (Backend Cloud)
    │   └── 데이터·AI 파이프라인 → 03번 (Data & AI)
    ↓
Step 3. 담당 에이전트 — 작업 수행
    │   코드 작성, 수정, 테스트를 수행한다.
    │   자율 검증: lint, build, test 직접 실행
    ↓
Step 4. 담당 에이전트 → 04번 보고
    │   작업 결과, 변경 파일, 발견된 이슈를 보고한다.
    ↓
Step 5. 04번 Tech Lead PM — 취합 및 브리핑
    │   보고를 취합하고 우선순위를 매겨 표준 보고 형식으로 정리한다.
    ↓
Step 6. 사용자 최종 확인
    │   사용자가 결과를 확인하고 피드백을 제공한다.
    ↓
Step 7. 문서 갱신
        PROGRESS.log 기록, 필요 시 CLAUDE.md 갱신
```

---

## SOP 2: 긴급 이슈 대응

보안 취약점, 서비스 장애, 데이터 유실 위험 발생 시 적용한다.

```
Step 1. 이슈 감지
    │   01~03번 에이전트 또는 04번이 문제를 발견한다.
    ↓
Step 2. 즉시 수정 조치
    │   해당 에이전트가 긴급 패치를 적용한다.
    │   (보안 취약점: XSS, key 노출, injection 등)
    ↓
Step 3. 04번에게 긴급 보고
    │   [High Priority] 태그로 즉시 보고한다.
    │   내용: 발견 내용, 영향 범위, 수정 조치, 잔존 리스크
    ↓
Step 4. 04번 → 사용자 즉시 알림
    │   Tech Lead PM이 사용자에게 긴급 브리핑을 수행한다.
    ↓
Step 5. 사후 조치
        원인 분석, 재발 방지 대책 수립, PROGRESS.log 기록
```

---

## SOP 3: 승인 필요 사항 처리

비용 발생, 아키텍처 변경, 보안 규칙 변경 등 사용자 승인이 필요한 경우 적용한다.

```
Step 1. 변경 필요성 감지
    │   담당 에이전트가 승인 대상 변경을 식별한다.
    ↓
Step 2. 04번에게 상신
    │   변경 사유, 영향 분석, 대안, 예상 비용을 보고한다.
    ↓
Step 3. 04번 — 영향 분석 및 정리
    │   사용자에게 간결한 승인 요청서를 작성한다.
    │   형식: [무엇을] [왜] [예상 비용/영향] [대안]
    ↓
Step 4. 사용자 승인/거부
    │   ├── 승인 → 해당 에이전트에 실행 지시
    │   └── 거부 → 대안 검토 또는 보류
    ↓
Step 5. 결과 기록
        PROGRESS.log에 승인 내역 기록
```

### 승인 필요 항목 기준

| 카테고리 | 구체적 예시 |
|---------|-----------|
| 비용 발생 | 새 API 구독, AWS 리소스 증설, 유료 서비스 |
| 아키텍처 변경 | DB 스키마 수정, 서비스 레이어 추가, 프레임워크 교체 |
| 보안 규칙 변경 | Firebase 규칙 수정, IAM 정책, 인증 흐름 |
| 외부 서비스 추가 | 새 API 연동, 대형 라이브러리 도입 |
| 데이터 구조 변경 | RTDB 경로 변경, Firestore 컬렉션 변경 |

---

## SOP 4: 문서 갱신 흐름

작업 완료 후 문서 동기화 프로세스이다.

```
작업 완료
    ↓
Step 1. PROGRESS.log 기록
    │   날짜, 작업 내용, 결과, 다음 할 일 형식으로 추가한다.
    ↓
Step 2. CLAUDE.md 갱신 여부 판단
    │   ├── 기술 스택 변경 → 갱신 필요
    │   ├── 디렉터리 구조 변경 → 갱신 필요
    │   ├── 행동 수칙 추가 → 갱신 필요
    │   └── 코드만 변경 → 갱신 불필요
    ↓
Step 3. ROADMAP.md 업데이트
    │   Phase별 체크박스 갱신 (완료 항목 체크)
    ↓
Step 4. AGENT_DIRECTORY.md 갱신 (에이전트 변동 시)
        새 에이전트 추가, 역할 변경 시에만 갱신한다.
```

---

## SOP 5: 버전 관리 및 배포 흐름

코드 변경 사항을 Git으로 관리하고 운영 환경에 배포할 때 적용한다.
**모든 커밋 및 병합 권한은 02번(Backend Cloud)이 단독으로 보유한다.**

```
Step 1. 02번 — 작업용 브랜치 생성
    │   기능 개발: feat/기능명  (예: feat/news-dashboard)
    │   버그 수정: fix/이슈명   (예: fix/firebase-auth-error)
    │   핫픽스:   hotfix/내용   (예: hotfix/lambda-timeout)
    ↓
Step 2. 개발 에이전트(01/03) — 코드 작성
    │   각 담당 에이전트가 해당 브랜치에서 코드를 작성한다.
    │   직접 커밋은 불가 — 변경 파일 목록을 02번에 전달한다.
    ↓
Step 3. 04번(Tech Lead PM) — 코드 검수
    │   변경 사항을 리뷰하고 통과/반려 판정을 내린다.
    │   검수 기준: 보안, 타입 안전성, 에러 핸들링, 테스트
    ↓
Step 4. 02번 — 한글 컨벤션 커밋 및 병합
    │   아래 커밋 메시지 템플릿을 엄수하여 커밋한다.
    │
    │   [Feat]: 새로운 기능 추가
    │   [Fix]: 버그 수정
    │   [Docs]: 문서 수정 (README.md, CLAUDE.md 등)
    │   [Style]: 코드 포맷팅, 변경 없는 UI 수정
    │   [Refactor]: 코드 리팩토링
    │   [Test]: 테스트 코드 추가 및 수정
    │   [Chore]: 빌드 태스크, 패키지 매니저 수정
    │
    │   커밋 후 main 브랜치에 병합(Merge)을 실행한다.
    │   병합 후 CI/CD(GitHub Actions)가 자동으로 Lambda 배포를 시작한다.
    ↓
Step 5. 04번(Tech Lead PM) — 최종 보고
        커밋 내역, 배포 결과, 변경 요약을 사용자에게 브리핑한다.
```

### 브랜치 네이밍 규칙

| 구분 | 형식 | 예시 |
|------|------|------|
| 기능 개발 | `feat/기능명` | `feat/news-dashboard`, `feat/watchlist-filter` |
| 버그 수정 | `fix/이슈명` | `fix/firebase-auth-error`, `fix/lambda-timeout` |
| 핫픽스 | `hotfix/내용` | `hotfix/api-key-leak` |
| 문서 갱신 | `docs/내용` | `docs/update-readme` |
| 리팩토링 | `refactor/내용` | `refactor/ai-service-cleanup` |

### 커밋 메시지 예시

```bash
git commit -m "[Feat]: 뉴스 피드 대시보드 UI 컴포넌트 추가"
git commit -m "[Fix]: Firebase onValue 구독 cleanup 누락 수정"
git commit -m "[Chore]: requirements.txt에서 litellm 제거"
git commit -m "[Docs]: CLAUDE.md 행동 수칙 업데이트"
git commit -m "[Refactor]: ai_service.py 쿼터 관리 로직 분리"
```

### 직접 커밋 금지 대상

| 에이전트 | 직접 커밋 | 이유 |
|---------|---------|------|
| 01번 (Frontend) | ❌ 금지 | 02번 감독 필수 |
| 02번 (Backend Cloud) | ✅ 허용 | 커밋/병합 총괄 책임자 |
| 03번 (Data/AI) | ❌ 금지 | 02번 감독 필수 |
| 04번 (Tech Lead PM) | ❌ 금지 | 보고·QA 전담 역할 |

---

## 보고 형식 표준

### 04번 Tech Lead PM → 사용자 보고
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[04 Tech Lead PM 보고]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ High Priority (사용자 승인 필요)
  - [항목] — [이유] — [필요한 결정]

■ 진행 완료 (참고)
  - [작업 내용] — [담당] — [결과 요약]

■ 진행 중 (모니터링)
  - [작업 내용] — [담당] — [예상 완료]

■ 리스크/이슈
  - [이슈] — [영향도] — [대응 방안]

■ 다음 단계 제안
  - [제안] — [우선순위] — [예상 소요]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 01~03번 에이전트 → 04번 보고
```
[에이전트 번호] 작업 보고
- 작업 내용: ...
- 변경 파일: ...
- 테스트 결과: pass / fail
- 발견된 이슈: ...
- 사용자 승인 필요 여부: 예 / 아니오
```

---

## SOP 6: 데이터베이스 추가/이관 절차

새 DB 서비스 연동 또는 기존 DB 이관 시 적용한다.
**모든 DB 관련 결정은 SOP 3(승인 필요 사항)을 통해 사용자 승인 후 진행한다.**

### 승인 필요 항목 (SOP 3 경유)
- 새 DB 서비스 추가 (비용 발생 가능)
- 기존 DB 스키마/경로 변경 (데이터 정합성 위험)
- Firebase Security Rules 변경
- 환경 변수 신규 추가 (GitHub Secrets 포함)

### DB 추가 절차 (예: Supabase 신규 연동)

```
Step 1. 03번(데이터/AI) — 테이블 스키마 설계
    │   인덱스, 파티셔닝, RLS 정책 포함하여 설계안 작성
    │   → 04번에 상신
    ↓
Step 2. 04번 Tech Lead PM — 사용자 승인 요청 (SOP 3)
    │   [무엇을] [왜] [예상 비용/영향] [대안]
    ↓
Step 3. 사용자 승인 후 → 02번(Backend Cloud) — 인프라 연결 설정
    │   GitHub Secrets 추가 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 등)
    │   Lambda 연결 풀러 설정 (Supavisor 포트 6543, Transaction mode)
    ↓
Step 4. 04번(Tech Lead PM) — 스키마 리뷰
    │   데이터 무결성, RLS 보안, 인덱스 효율 검토
    ↓
Step 5. 02번(Backend Cloud) — Lambda 코드 연동
    │   psycopg2-binary 또는 supabase 클라이언트 추가
    │   requirements.txt 크기 확인 (250MB 제한)
    ↓
Step 6. 로컬 테스트 (test_run.py) 후 커밋·배포
    ↓
Step 7. 기존 DB 제거는 신규 DB 안정화 확인 후 진행
        (최소 1주일 안정 운영 확인 후)
```

### Firebase → Supabase 단계적 이관 기준

| 이관 항목 | 조건 | 예상 Phase |
|---------|------|-----------|
| Firestore → Supabase | Supabase stock_history 안정 운영 1주일 후 | Phase 3 중반 |
| Firebase Auth → Supabase Auth | Phase 4, Supabase Realtime 성숙도 확인 후 | Phase 4 |
| Firebase RTDB → Supabase Realtime | 지연시간 < 200ms 검증 후 (현재 유지) | Phase 4 이후 |

### 패키지 크기 가이드라인

| 라이브러리 | 크기 | 허용 여부 |
|---------|------|---------|
| psycopg2-binary | ~5MB | ✅ 허용 |
| supabase (Python) | ~10MB | ✅ 허용 |
| firebase-admin | ~25MB | ✅ 허용 (기존) |
| litellm | ~120MB+ | ❌ 금지 |
| pandas | ~50MB | ⚠️ 신중 검토 |

---

## 에이전트 호출 가이드

| 작업 유형 | 호출 에이전트 | 예시 |
|----------|-------------|------|
| UI 컴포넌트 신규/수정, 디자인 개편 | 01번 | 대시보드 카드 추가, 반응형 수정, 전면 UI 개편 |
| 백엔드 로직 수정, 인프라 작업 | 02번 | 서비스 함수 추가, CI/CD 수정, Lambda 설정, Git 커밋 |
| AI 요약 품질 개선, 데이터 수집 | 03번 | 프롬프트 수정, 모델 라우팅 변경, 데이터 파이프라인 |
| 전체 상황 브리핑, 코드 리뷰, 승인 요청 | 04번 | 진행 보고, 보안 점검, 빌드 검증, 의사결정 |
