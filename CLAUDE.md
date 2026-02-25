# CLAUDE.md — stock-news-sync

> 이 파일은 Claude Code가 세션마다 자동으로 읽는 프로젝트 컨텍스트 파일입니다.
> 수정 시 실제 코드 구조와 동기화를 유지하세요.

---

## 프로젝트 개요

**stock-news-sync**는 한국어/영어 AI 투자 브리핑 플랫폼입니다.
- 주식 시장 데이터(yfinance)와 뉴스(Tavily API)를 수집
- Groq / Google Gemini LLM으로 카테고리별 AI 요약 생성
- Firebase Realtime Database에 저장 → Next.js 대시보드에 실시간 표시
- AWS Lambda로 자동 실행 (GitHub Actions CI/CD)

---

## 기술 스택

### Frontend
- **Framework**: Next.js 16.1.5 (App Router, React 19, TypeScript 5)
- **Styling**: Tailwind CSS v4 + PostCSS
- **Icons**: lucide-react
- **DB Client**: Firebase SDK v12 (Realtime Database 실시간 구독)
- **Auth**: Firebase Auth (Google Sign-In)
- **Linting**: ESLint v9 (eslint-config-next / core-web-vitals)

### Backend (Data Sync Engine)
- **Runtime**: Python 3.11 (AWS Lambda, ap-northeast-2)
- **Market Data**: yfinance (Yahoo Finance API)
- **News Search**: Tavily API (`topic="news"`, max_results=3)
- **AI/LLM**: OpenAI SDK — Groq(base_url 변경) + Google Gemini 연결
- **DB**: Firebase Admin SDK (RTDB + Firestore 이중 저장)
- **Env**: python-dotenv

### Infrastructure
- **Serverless**: AWS Lambda (Python 3.11 런타임)
- **CI/CD**: GitHub Actions → S3 → Lambda 업데이트
- **Build**: manylinux2014_x86_64 아키텍처 빌드 (Lambda 호환)
- **Package Limit**: 250MB (LiteLLM 등 무거운 패키지 사용 금지)
- **Database**: Firebase Realtime Database + Firestore
- **Region**: ap-northeast-2 (서울)

---

## 디렉터리 구조

```
stock-news-sync/
├── CLAUDE.md                        # 이 파일 (Claude Code 자동 로드)
├── .claude/
│   ├── agents/                      # 서브에이전트 프롬프트
│   │   ├── 01_frontend_agent.md
│   │   ├── 02_backend_agent.md
│   │   ├── 03_data_ai_agent.md
│   │   ├── 04_qa_agent.md
│   │   ├── 05_devops_sre_agent.md   # DevOps/SRE 인프라 운영
│   │   └── 06_chief_of_staff_agent.md  # 비서실장 (중앙 보고)
│   └── worktrees/                   # Claude Code 병렬 에이전트 워크트리
├── docs/
│   ├── operations/                  # 운영 관리 문서 (06번 관리)
│   │   ├── AGENT_DIRECTORY.md       # 에이전트 인사 관리 카드
│   │   └── PLAYBOOK.md             # 표준 협업 프로세스 (SOP)
│   └── status/
│       ├── ROADMAP.md               # 프로젝트 로드맵 (Phase별 진행)
│       └── PROGRESS.log             # 작업 진행 로그
├── vercel.json                      # Vercel 빌드 설정 (rootDirectory: frontend)
├── .github/
│   ├── workflows/
│   │   ├── sync.yml                 # Lambda 배포 파이프라인 (frontend-check job 포함)
│   │   └── frontend-deploy.yml      # Vercel 프론트엔드 배포 파이프라인
│   └── scripts/make_lambda_env.py   # Lambda 환경변수 JSON 생성 스크립트
├── backend/
│   ├── main.py                      # Lambda 핸들러 진입점 (lambda_handler)
│   ├── test_run.py                  # 로컬 테스트 실행
│   ├── requirements.txt             # Python 의존성
│   ├── .env                         # API 키 (gitignored)
│   ├── serviceAccount.json          # Firebase 서비스 계정 (gitignored)
│   ├── config/
│   │   ├── tickers.py               # 포트폴리오/관심종목/키워드 정의
│   │   └── models.py                # AI 모델 라우팅 설정
│   └── services/
│       ├── ai_service.py            # LLM 요약 (Groq/Gemini 팔백)
│       ├── db_service.py            # Firebase RTDB + Firestore 저장
│       ├── market_service.py        # yfinance 시장 데이터
│       └── news_service.py          # Tavily 뉴스 검색
└── frontend/
    ├── app/
    │   ├── layout.tsx               # 루트 레이아웃 (lang="ko", 한국어 메타데이터)
    │   └── page.tsx                 # 메인 대시보드 (7개 컴포넌트 조합)
    ├── components/
    │   ├── AdBanner.tsx             # 광고 배너 컴포넌트 (top-banner/side-banner/in-feed)
    │   ├── dashboard/
    │   │   └── MarketIndexCard.tsx  # 시장 지수/지표 표시 카드 (macro/index variant)
    │   ├── portfolio/
    │   │   └── StockRow.tsx         # 주식 1행 컴포넌트 (portfolio/watchlist variant)
    │   ├── news/
    │   │   ├── AISummaryCard.tsx    # AI 요약 구조화 표시 (호재/악재/중립 파싱)
    │   │   ├── NewsCard.tsx         # 뉴스 카드 (상대 시간 포맷, rel=noopener)
    │   │   └── NewsFeedSection.tsx  # 탭 네비게이션 + AI 요약 + 뉴스 목록 통합
    │   └── layout/
    │       └── Header.tsx           # 스티키 헤더 (2단: Macro 지표 + 시장 지수 + 인증)
    ├── lib/
    │   ├── firebase.ts              # Firebase 클라이언트 초기화 (auth, db, googleProvider)
    │   └── types.ts                 # 공통 타입 인터페이스 (MarketValue, StockData, etc.)
    ├── next.config.ts
    ├── tsconfig.json
    ├── package.json
    └── .env.local                   # Firebase 클라이언트 키 (gitignored)
```

---

## 환경 변수

### `backend/.env` (로컬 개발)
```
GROQ_API_KEY=...
GEMINI_API_KEY=...
TAVILY_API_KEY=...
FIREBASE_SERVICE_ACCOUNT=<JSON 문자열 또는 파일 경로>
FIREBASE_DATABASE_URL=https://stock-news-sync-default-rtdb.firebaseio.com
```

### `frontend/.env.local` (로컬 개발)
```
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=stock-news-sync
NEXT_PUBLIC_FIREBASE_DATABASE_URL=...
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
```

### GitHub Secrets (Lambda 배포 시 자동 주입)
`GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `FIREBASE_SERVICE_ACCOUNT`, `FIREBASE_DATABASE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

---

## 코딩 컨벤션

### Python (Backend)
- **서비스 레이어 패턴**: 비즈니스 로직은 `services/` 내 함수로 분리
- **로깅**: `logging` 모듈 사용, `print()` 지양
- **Type hints**: 함수 시그니처에 타입 힌트 권장
- **에러 핸들링**: 개별 티커/API 실패는 `try/except`로 건너뜀 (전체 실행 중단 방지)
- **Firebase 쓰기**: `update()` 사용 (`set()` 금지 — 기존 데이터 덮어씌움 방지)

### TypeScript (Frontend)
- **App Router**: Server Component 기본, `"use client"` 필요한 경우만 명시
- **Strict mode**: `any` 타입 사용 금지
- **Tailwind**: 인라인 style 속성 지양, Tailwind 클래스만 사용
- **Firebase 구독**: `onValue()` 사용, 컴포넌트 언마운트 시 `off()` cleanup 필수

### 커밋 메시지
```
feat: 새 기능 추가
fix: 버그 수정
refactor: 코드 구조 개선 (기능 변경 없음)
docs: 문서 수정
chore: 빌드/설정 변경
```
예시: `fix: litellm → openai SDK로 교체 (Lambda 250MB 제한 초과 해결)`

---

## 행동 수칙 (Claude Code 필수 준수)

1. **파일 수정 전 반드시 읽기**: 코드를 이해한 후 수정. 읽지 않고 추측으로 수정 금지.
2. **API 키 절대 하드코딩 금지**: `.env` 파일 또는 환경변수 경유. 코드/커밋에 포함 금지.
3. **Lambda 배포는 GitHub Actions 경유만**: 직접 `aws lambda update-function-code` 실행 금지.
4. **Firebase 데이터 구조 변경 전 `db_service.py` 검토**: RTDB 경로(`/feed/`) 일관성 유지 필수.
5. **패키지 추가 시 250MB 제한 확인**: `requirements.txt`에 추가 전 패키지 크기 확인. LiteLLM 같은 대형 패키지 금지.
6. **보안 취약점 발견 즉시 수정 후 보고**: XSS, key 노출, injection 등 발견 시 수정 우선.
7. **과도한 추상화 금지**: 현재 요구사항에 필요한 최소한의 코드만 작성.
8. **테스트 없이 운영 데이터 구조 변경 금지**: `test_run.py`로 로컬 검증 후 커밋.
9. **중앙 보고 체계 준수**: 01~05번 에이전트는 직접 사용자에게 보고하지 않고,
   반드시 06번(비서실장)을 경유하여 보고한다.
   06번은 사용자가 살펴봐야 할 High Priority 항목을 선별하여 브리핑한다.
10. **Git 커밋 규칙 엄수**: 모든 에이전트(01~04)는 코드 수정 후 직접 커밋하지 않는다.
    반드시 05번 에이전트의 감독하에, 아래 한글 커밋 메시지 템플릿을 사용하여 커밋한다.
    ```
    [Feat]: 새로운 기능 추가
    [Fix]: 버그 수정
    [Docs]: 문서 수정 (README.md, CLAUDE.md 등)
    [Style]: 코드 포맷팅, 변경 없는 UI 수정
    [Refactor]: 코드 리팩토링
    [Test]: 테스트 코드 추가 및 수정
    [Chore]: 빌드 태스크, 패키지 매니저(requirements.txt, package.json 등) 수정
    ```

---

## 자율 작업 및 보고 규칙

1. **자율 검증**: 코드 수정 후 `npm run lint`(프론트), `python test_run.py`(백엔드) 등
   빌드/린트 테스트를 직접 수행하여 오류가 없는지 확인한다.
2. **문서 동기화**: 의미 있는 작업이 완료되면 `docs/status/PROGRESS.log`를 업데이트하여
   사용자에게 현재 상황을 기록한다.
3. **문맥 유지**: 기술적 변화(새 라이브러리 추가, 구조 변경 등)가 발생하면
   `CLAUDE.md`를 갱신하여 다음 세션의 AI가 최신 상태를 인지하도록 한다.
4. **중앙 보고**: 모든 에이전트의 작업 결과는 06번(비서실장)이 취합하여
   우선순위를 매기고 사용자에게 최종 보고한다.

---

## 자주 쓰는 명령어

```bash
# Frontend 개발 서버
cd frontend && npm run dev        # http://localhost:3000

# Frontend 린트
cd frontend && npm run lint

# Backend 로컬 테스트
cd backend && python test_run.py

# Backend 전체 실행 (Lambda 핸들러 직접 실행)
cd backend && python main.py

# Lambda 배포 (CI/CD 트리거)
git push origin main              # GitHub Actions 자동 실행
```

---

## AI 모델 라우팅 (참고)

`backend/config/models.py` 에 정의:

| 카테고리 | 1순위 | 2순위 | 3순위 |
|---------|------|------|------|
| macro | Gemini 2.5 Pro | Groq GPT-OSS | Gemini Flash |
| portfolio | Groq GPT-OSS | Gemini Pro | Llama 3.1 |
| watchlist | Llama 3.1 | Gemini Flash | Groq GPT-OSS |

- **공통 설정**: `MAX_TOKENS=1000`, `TEMPERATURE=0.2`
- **쿼터 관리**: `_quota_exceeded_models` — 세션 내 재시도 방지

---

## Firebase 데이터 구조

### Realtime Database (`/feed/`)
```
/feed/
  market_indices/     # KOSPI, KOSDAQ, S&P500, NASDAQ, USD/KRW, US10Y, BTC
  stock_data/         # 거래량 상위 15개 종목 (US + KR)
  news/
    macro/            # 거시경제 AI 브리핑
    portfolio/        # 포트폴리오 종목 뉴스
    watchlist/        # 관심 종목 뉴스
```

### Firestore (`market_feeds/latest`)
- RTDB와 동일한 데이터의 백업 저장소

---

## Phase 3 DB 전략 (2026-02-25 전 에이전트 회의 결정)

### 현재 DB 구조
- **Firebase RTDB**: 실시간 시장 데이터 표시 (유지)
- **Firestore**: 동일 데이터 백업 저장 (Phase 3 중반 제거 예정)

### Phase 3 추가 예정
- **Supabase PostgreSQL**: 주가 히스토리 + 사용자 Watchlist
  - Connection: Supavisor 포트 6543 (Lambda 연결 풀링, Transaction mode)
  - 테이블: `stock_history` (OHLCV 60일), `watchlist` (사용자별)
  - RLS: user_id 기반 Row Level Security 적용

### 이관 원칙
1. **Firebase RTDB**: 실시간 구독 특화, 장기 유지
2. **Firestore**: Supabase로 대체 후 제거 (Phase 3 안정화 후)
3. **Firebase Auth**: Phase 4 이후 Supabase Auth 이관 검토

### 환경 변수 (Phase 3 추가 예정)
```
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...
```
