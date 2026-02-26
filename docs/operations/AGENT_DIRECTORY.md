# 에이전트 인사 관리 카드

> 관리 주체: **04번 Tech Lead PM**
> 최종 수정: 2026-02-27
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

## 역할 분리 원칙

| 구분 | 01번 (프론트엔드) | 02번 (백엔드+클라우드) | 03번 (데이터+AI) | 04번 (관리) |
|------|---------------|---------------------|----------------|------------|
| 초점 | 디자인·UI/UX | 코드 로직 + 인프라 운영 | 데이터·AI 파이프라인 | QA + 보고 |
| Firebase | 클라이언트 구독 | Admin SDK 쓰기, 보안 규칙 | — | 경로 일관성 검증 |
| Lambda | — | 핸들러 코드 작성 + 패키징/배포 | 서비스 함수 | 패키지 크기 검사 |
| CI/CD | — | 워크플로우 관리 | — | 배포 결과 모니터링 |
| Git | 코드 작성 (커밋 불가) | **커밋/병합 권한** | 코드 작성 (커밋 불가) | QA 검수 후 승인 |
| 사용자 보고 | ❌ 04번 경유 | ❌ 04번 경유 | ❌ 04번 경유 | ✅ 직접 보고 |

---

## 아카이브

폐지된 에이전트 파일은 `.claude/agents/archive/` 에 보관됩니다.

| 파일 | 폐지 이유 | 통합 대상 |
|------|---------|---------|
| `04_qa_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 04 Tech Lead PM |
| `05_devops_sre_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 02 Backend Cloud |
| `06_chief_of_staff_agent.md` | 4-Agent 체제 개편 (2026-02-27) | → 04 Tech Lead PM |
