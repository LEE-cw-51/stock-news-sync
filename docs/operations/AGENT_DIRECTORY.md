# 에이전트 인사 관리 카드

> 관리 주체: **04번 Tech Lead PM**
> 최종 수정: 2026-03-21
> 파일 위치: `.claude/agents/`

---

## 조직도

```
                    ┌─────────────────┐
                    │    사용자 (You)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ 04 Tech Lead PM  │
                    │  (QA + 보고 총괄)│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
   ┌─────▼─────┐     ┌───────▼───────┐   ┌───────▼───────┐
   │ 01 프론트  │     │ 02 백엔드+클라우드│   │  03 데이터/AI  │
   │ (UI/UX)  │     │ (코드+인프라+Git)│   │  (데이터+LLM)  │
   └───────────┘     └───────────────┘   └───────────────┘

           ┌─────────────────────────────────┐
           │  05 DB Management (전문가 역할)   │
           │  (스키마·RLS 감사·DB 거버넌스)    │
           │  → DB 관련 작업 시 04번이 호출   │
           └─────────────────────────────────┘
```

---

## 01 — Frontend Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/01_frontend_agent.md` |
| **페르소나** | UI/UX 디자인 전문 프론트엔드 엔지니어 |
| **담당 영역** | 디자인 시스템 구축, 전면 UI/UX 개편 주도, Next.js App Router, Tailwind CSS v4, Firebase RTDB 구독 |
| **핵심 파일** | `app/page.tsx`, `app/globals.css`, `components/`, `lib/firebase.ts`, `lib/types.ts` |
| **호출 시점** | UI 컴포넌트 개발, 반응형 레이아웃, 디자인 개편, Firebase 실시간 구독, 스타일링 작업 |

---

## 02 — Backend & Cloud Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/02_backend_cloud_agent.md` |
| **페르소나** | 백엔드 및 클라우드(DevOps) 엔지니어 |
| **담당 영역** | Python 백엔드 핵심 로직(`main.py`), Firebase Admin 쓰기 패턴, AWS Lambda 패키징/배포, GitHub Actions CI/CD, 환경변수 스크립트, **Git 커밋/병합 총괄** |
| **핵심 파일** | `backend/main.py`, `backend/services/`, `backend/requirements.txt`, `.github/workflows/*.yml`, `.github/scripts/` |
| **호출 시점** | 백엔드 로직 수정, 서비스 함수 추가, CI/CD 수정, Lambda 설정, 장애 대응, Git 커밋 실행 |

---

## 03 — Data & AI Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/03_data_ai_agent.md` |
| **페르소나** | 데이터 수집 및 AI 프롬프트 엔지니어 |
| **담당 영역** | 외부 API 연동(Tavily 뉴스, yfinance), LLM(Groq/Gemini) 프롬프트 최적화, 할루시네이션 방지 시스템, 모델 쿼터 관리 |
| **핵심 파일** | `backend/services/ai_service.py`, `backend/services/market_service.py`, `backend/services/news_service.py`, `backend/config/models.py`, `backend/config/tickers.py` |
| **호출 시점** | AI 모델 라우팅 변경, 프롬프트 개선, 데이터 수집 로직 수정, 할루시네이션 방지, 할루시네이션 방지 |

---

## 04 — Tech Lead PM Agent (관리 주체)

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/04_tech_lead_pm_agent.md` |
| **페르소나** | 테크 리드(Tech Lead) 겸 비서실장(PM) |
| **담당 영역** | 01~03번 작업물 통합 QA(코드 리뷰·보안 취약점 스캔), 아키텍처·비용 리스크 필터링, 사용자 최종 브리핑 및 승인 요청, 문서 관리 |
| **핵심 파일** | `docs/operations/`, `docs/status/`, `CLAUDE.md` |
| **호출 시점** | 전체 작업 상황 브리핑, 의사결정 필요 시, 보안/장애 이슈, 팀 운영 문서 갱신 |

---

## 05 — DB Management Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/05_db_management_agent.md` |
| **페르소나** | 데이터베이스 거버넌스 및 스키마 관리 전문가 |
| **담당 영역** | Firebase RTDB 경로 일관성, Supabase 스키마/RLS 감사, 심볼 키 정규화, DDL 마이그레이션 초안, `docs/reference/DATA_SCHEMA.md` 단독 유지보수 |
| **핵심 파일** | `backend/db/supabase_schema.sql`, `docs/reference/DATA_SCHEMA.md`, `backend/services/db_service.py` (감사 전용, 수정 불가) |
| **호출 시점** | 아래 트리거 조건 참조 |

### 05번 호출 트리거 조건

다음 중 하나라도 해당하면 **04번이 05번을 호출**한다:

| 트리거 | 예시 |
|--------|------|
| Supabase 테이블/컬럼 추가·변경 | 새 테이블 설계, 컬럼 타입 변경 |
| Firebase RTDB 경로 변경 | `/feed/` 하위 경로 신설·삭제·이름 변경 |
| RLS 정책 신규·수정 | `stock_history` RLS 추가 |
| 심볼 키 정규화 로직 변경 | `.` → `_` 규칙 수정, 새 접미사 처리 |
| DB 보안 감사 요청 | 분기별 감사, 이슈 탐지 후 |
| `db_service.py` 경로 수정 전 | Firebase ref 경로 포함 작업 전 사전 검토 |
| `DATA_SCHEMA.md` 갱신 필요 | 스키마 변경 완료 후 문서 동기화 |

**05번을 호출하지 않아도 되는 경우**: 단순 Python 로직 수정(DB 경로·스키마 무관), 프론트엔드 UI 변경, AI 프롬프트·모델 라우팅 변경

---

## 역할 분리 원칙

| 구분 | 01번 (프론트엔드) | 02번 (백엔드+클라우드) | 03번 (데이터+AI) | 04번 (관리) | 05번 (DB 거버넌스) |
|------|---------------|---------------------|----------------|------------|-----------------|
| 초점 | 디자인·UI/UX | 코드 로직 + 인프라 운영 | 데이터·AI 파이프라인 | QA + 보고 | DB 설계·감사·문서화 |
| Firebase | 클라이언트 구독 | Admin SDK 쓰기, 보안 규칙 | — | 경로 일관성 검증 | 경로 거버넌스, 사전 검토 |
| Lambda | — | 핸들러 코드 작성 + 패키징/배포 | 서비스 함수 | 패키지 크기 검사 | — |
| CI/CD | — | 워크플로우 관리 | — | 배포 결과 모니터링 | — |
| Git | 코드 작성 (커밋 불가) | **커밋/병합 권한** | 코드 작성 (커밋 불가) | QA 검수 후 승인 | 커밋 불가 (02번 수행) |
| 사용자 보고 | ❌ 04번 경유 | ❌ 04번 경유 | ❌ 04번 경유 | ✅ 직접 보고 | ❌ 04번 경유 |

### 핵심 파일 레벨 담당 (충돌 방지)

| 파일 | 주담당 | 보조 | 비고 |
|------|--------|------|------|
| `backend/main.py` | **02번** | — | Lambda 핸들러 진입점 |
| `backend/services/db_service.py` | **02번** | — | Firebase/Supabase 연결 |
| `backend/services/ai_service.py` | **03번** | 02번 (커밋만) | LLM 라우팅·프롬프트 |
| `backend/services/market_service.py` | **03번** | 02번 (커밋만) | yfinance 데이터 수집 |
| `backend/services/news_service.py` | **03번** | 02번 (커밋만) | Tavily 뉴스 수집 |
| `backend/config/models.py` | **03번** | 02번 (커밋만) | AI 모델 라우팅 설정 |
| `backend/config/tickers.py` | **03번** | 02번 (커밋만) | 종목·키워드 정의 |
| `frontend/app/`, `components/`, `lib/` | **01번** | 02번 (커밋만) | Next.js UI 전체 |
| `.github/workflows/` | **02번** | — | CI/CD 파이프라인 |

---

## 아카이브

폐지된 에이전트 파일은 `.claude/agents/archive/` 에 보관됩니다.

| 파일 | 폐지 이유 | 통합 대상 |
|------|---------|---------|
| `04_qa_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 04 Tech Lead PM |
| `05_devops_sre_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 02 Backend Cloud |
| `06_chief_of_staff_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 04 Tech Lead PM |
