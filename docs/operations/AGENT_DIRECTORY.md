# 에이전트 인사 관리 카드

> 관리 주체: **06번 비서실장 (Chief of Staff)**
> 최종 수정: 2025-02-25
> 파일 위치: `.claude/agents/`

---

## 조직도

```
                    ┌─────────────────┐
                    │    사용자 (You)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  06 비서실장      │
                    │  Chief of Staff  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐      ┌──────▼──────┐      ┌──────▼──────┐
  │ 01 프론트  │      │ 02 백엔드    │      │ 03 데이터/AI│
  │ Frontend  │      │ Backend     │      │ Data & AI   │
  └───────────┘      └─────────────┘      └─────────────┘
        │                    │
  ┌─────▼─────┐      ┌──────▼──────┐
  │ 04 QA     │      │ 05 DevOps   │
  │ 품질검증   │      │ SRE        │
  └───────────┘      └─────────────┘
```

---

## 01 — Frontend Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/01_frontend_agent.md` |
| **페르소나** | 토스(Toss)와 같은 유려한 금융 UX를 만드는 시니어 프론트엔드 엔지니어 |
| **담당 영역** | `frontend/` 전체 — Next.js App Router, Tailwind CSS v4, Firebase RTDB 구독 |
| **핵심 파일** | `app/page.tsx`, `components/`, `lib/firebase.ts` |
| **호출 시점** | UI 컴포넌트 개발, 반응형 레이아웃, Firebase 실시간 구독, 스타일링 작업 |

---

## 02 — Backend Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/02_backend_agent.md` |
| **페르소나** | AWS와 Firebase 인프라에 정통한 클라우드 아키텍트 |
| **담당 영역** | `backend/` 코드 로직 — Lambda 핸들러, 서비스 레이어, Firebase Admin SDK 쓰기 |
| **핵심 파일** | `main.py`, `services/`, `config/` |
| **호출 시점** | 백엔드 로직 수정, 서비스 함수 추가, API 연동, Firebase 데이터 쓰기 패턴 |

---

## 03 — Data & AI Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/03_data_ai_agent.md` |
| **페르소나** | 데이터 분석과 프롬프트 엔지니어링 전문가 |
| **담당 영역** | 금융 데이터 수집(yfinance), 뉴스 검색(Tavily), LLM 요약 파이프라인(Groq/Gemini) |
| **핵심 파일** | `services/ai_service.py`, `services/market_service.py`, `services/news_service.py`, `config/models.py`, `config/tickers.py` |
| **호출 시점** | AI 모델 라우팅 변경, 프롬프트 개선, 데이터 수집 로직, 할루시네이션 방지 |

---

## 04 — QA Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/04_qa_agent.md` |
| **페르소나** | 코드의 무결성을 검증하는 QA 엔지니어 |
| **담당 영역** | 코드 리뷰, 보안 취약점 스캔, 빌드 검증, TypeScript strict 검사 |
| **핵심 파일** | 전체 코드베이스 (보안 관점) |
| **호출 시점** | PR 리뷰, 배포 전 품질 게이트, 보안 점검, 버그 검수 |

---

## 05 — DevOps & SRE Agent

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/05_devops_sre_agent.md` |
| **페르소나** | 10년 차 시니어 DevOps 및 SRE 전문가 |
| **담당 영역** | AWS Lambda 배포/모니터링, CI/CD 워크플로우, Vercel 배포, Firebase 보안 규칙, GitHub Secrets 관리 |
| **핵심 파일** | `.github/workflows/sync.yml`, `.github/scripts/make_lambda_env.py`, `backend/requirements.txt` |
| **호출 시점** | 배포 파이프라인 수정, 인프라 장애 대응, 보안 규칙 변경, 패키지 크기 관리 |

---

## 06 — Chief of Staff Agent (관리 주체)

| 항목 | 내용 |
|------|------|
| **파일** | `.claude/agents/06_chief_of_staff_agent.md` |
| **페르소나** | 기업 비서실장 겸 비서팀장 |
| **담당 영역** | 01~05번 보고 취합, High Priority 선별, 승인 필터링, 운영 문서 관리 |
| **핵심 파일** | `docs/operations/`, `docs/status/`, `CLAUDE.md` |
| **호출 시점** | 전체 작업 상황 브리핑, 의사결정 필요 시, 팀 운영 문서 갱신 |

---

## 역할 분리 원칙

| 구분 | 02번 (백엔드) | 05번 (DevOps) |
|------|-------------|--------------|
| 초점 | 코드 로직 | 인프라 운영 |
| Lambda | 핸들러 코드 작성 | 패키징/배포/모니터링 |
| Firebase | 데이터 읽기/쓰기 코드 | 보안 규칙 설계 |
| CI/CD | — | 워크플로우 관리 |
| 환경변수 | 코드 내 사용 패턴 | Secrets 로테이션/관리 |
