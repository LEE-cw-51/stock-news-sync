# 프로젝트 디렉터리 구조

> 최종 업데이트: 2026-03-03

```
stock-news-sync/
├── CLAUDE.md                        # Claude Code 자동 로드 (세션 컨텍스트)
├── .claude/
│   ├── agents/                      # 서브에이전트 프롬프트
│   │   ├── 01_frontend_agent.md
│   │   ├── 02_backend_cloud_agent.md
│   │   ├── 03_data_ai_agent.md
│   │   ├── 04_tech_lead_pm_agent.md # Tech Lead PM (QA + 보고 총괄)
│   │   └── archive/                 # 폐지된 에이전트 보관
│   └── worktrees/                   # Claude Code 병렬 에이전트 워크트리
├── docs/
│   ├── operations/                  # 운영 관리 문서 (04번 관리)
│   │   ├── AGENT_DIRECTORY.md       # 에이전트 인사 관리 카드
│   │   └── PLAYBOOK.md              # 표준 협업 프로세스 (SOP)
│   ├── reference/                   # 기술 레퍼런스 (상세 스펙)
│   │   ├── PROJECT_STRUCTURE.md     # 이 파일
│   │   ├── ENV_VARS.md              # 환경 변수 목록
│   │   ├── CONVENTIONS.md           # 코딩 컨벤션 + 커밋 규칙
│   │   └── DATA_SCHEMA.md           # DB 스키마 + AI 모델 라우팅
│   └── status/
│       ├── ROADMAP.md               # 프로젝트 로드맵 (Phase별 진행)
│       ├── PROGRESS.log             # 작업 진행 로그
│       └── HANDOFF.md               # 세션 인수인계 문서
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
│   ├── db/
│   │   └── supabase_schema.sql      # Supabase PostgreSQL 스키마 (Phase 3)
│   ├── config/
│   │   ├── tickers.py               # 포트폴리오/관심종목/키워드 정의
│   │   └── models.py                # AI 모델 라우팅 설정
│   └── services/
│       ├── ai_service.py            # LLM 요약 (Groq/Gemini 팔백)
│       ├── db_service.py            # Firebase RTDB + Supabase REST 저장
│       ├── market_service.py        # yfinance 시장 데이터
│       └── news_service.py          # Tavily 뉴스 검색
└── frontend/
    ├── app/
    │   ├── layout.tsx               # 루트 레이아웃 (lang="ko", 한국어 메타데이터)
    │   └── page.tsx                 # 메인 대시보드 (7개 컴포넌트 조합)
    ├── components/
    │   ├── AdBanner.tsx             # 광고 배너 (top-banner/side-banner/in-feed)
    │   ├── dashboard/
    │   │   └── MarketIndexCard.tsx  # 시장 지수/지표 표시 카드 (macro/index variant)
    │   ├── chart/
    │   │   └── StockChart.tsx       # 60일 OHLCV 캔들스틱 차트 (Supabase 조회, "use client")
    │   ├── portfolio/
    │   │   └── StockRow.tsx         # 주식 1행 컴포넌트 (portfolio/watchlist variant, 차트 토글)
    │   ├── news/
    │   │   ├── AISummaryCard.tsx    # AI 요약 구조화 표시 (호재/악재/중립 파싱)
    │   │   ├── NewsCard.tsx         # 뉴스 카드 (상대 시간 포맷, rel=noopener)
    │   │   └── NewsFeedSection.tsx  # 탭 네비게이션 + AI 요약 + 뉴스 목록 통합
    │   └── layout/
    │       └── Header.tsx           # 스티키 헤더 (2단: Macro 지표 + 시장 지수 + 인증)
    ├── lib/
    │   ├── firebase.ts              # Firebase 클라이언트 초기화 (auth, db, googleProvider)
    │   ├── supabase.ts              # Supabase 클라이언트 (ANON_KEY, 차트 데이터 조회용)
    │   └── types.ts                 # 공통 타입 인터페이스 (StockHistory, MarketValue, StockData 등)
    ├── next.config.ts
    ├── tsconfig.json
    ├── package.json
    └── .env.local                   # Firebase 클라이언트 키 (gitignored)
```
