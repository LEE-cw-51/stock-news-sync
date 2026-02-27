# Stock-News-Sync 로드맵

## Phase 1: 뉴스 동기화 엔진 ✅ 완료
- [x] Tavily API 기반 뉴스 수집 엔진 구축
- [x] yfinance 기반 시장 지표 및 종목 데이터 수집
- [x] Firebase(RTDB + Firestore)를 활용한 데이터 영속성 확보
- [x] 멀티 LLM(Groq, Gemini) 연동 및 429 에러 대응 로직 구현
- [x] 카테고리별 AI 모델 라우팅 (macro/portfolio/watchlist)
- [x] AWS Lambda + GitHub Actions CI/CD 배포 파이프라인

## Phase 2: 프론트엔드 대시보드 ✅ 완료 (2026-02-25)
- [x] 운영 안정성 강화: DevOps/SRE 에이전트 및 비서실장 중심 의사결정 체계 구축
- [x] FIREBASE_DATABASE_URL Lambda 환경변수 정식 주입 (하드코딩 폴백 제거)
- [x] CI 프론트엔드 빌드 검증 게이트 추가 (frontend-check job 병렬 실행, ESLint 0 warnings 엄격 모드)
- [x] Vercel 배포 파이프라인 구성 (vercel.json + GitHub Actions frontend-deploy.yml, 공식 CLI)
- [x] Firebase Auth Google 로그인 UI 연동 (헤더 로그인/로그아웃 버튼)
- [x] layout.tsx 메타데이터 수정 (title: "Stock News Sync", lang: "ko")
- [x] Next.js 16 기반 뉴스 피드 UI 구현 (7개 컴포넌트 분리 + 탭 네비게이션)
- [x] AI 요약 구조화 표시 (호재/악재/중립 뱃지 + 불렛 파싱, 라이브러리 없이 순수 파싱)
- [x] 반응형 대시보드 레이아웃 (모바일 1열 / 데스크톱 2열, Tailwind md: 브레이크포인트)
- [x] 코드 품질 개선 (타입 분리 lib/types.ts, rel="noopener", aria-label 접근성)

> ※ 아래 2개 항목은 Phase 3으로 공식 이관 (2026-02-25 에이전트 회의 결정)
> - 주가 시각화 차트: 히스토리 수집 인프라 선행 필요 → Phase 3 Step 3
> - Watchlist 개인 관리: Lambda tickers.py 전면 수정 필요 → Phase 3 Step 4

## Phase 3: 개인화 + 데이터 고도화 (예정)
> **DB 전략**: Firebase RTDB 유지 + Supabase PostgreSQL 신규 추가 (2026-02-25 전 에이전트 회의 결정)

### Step 1 — Supabase 연동 기반 구축 ✅ 완료
- [x] Supabase 프로젝트 생성 및 환경변수 설정
- [x] PostgreSQL 테이블 설계: `stock_history`, `watchlist`, `users`
- [x] Lambda에 psycopg2-binary 추가 (Supabase 연결, Supavisor 포트 6543 경유)
- [x] GitHub Secrets에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` 추가

### Step 2 — 주가 히스토리 수집 ✅ 완료
- [x] backend: yfinance `.history(period="60d")` 데이터 수집 로직 추가
- [x] Lambda 실행 시 stock_history 테이블에 UPSERT (ON CONFLICT DO UPDATE)
- [x] Firestore 이중 저장 로직 제거 (Supabase로 대체)

### Step 3 — 차트 시각화 ✅ 완료 (2026-02-27)
- [x] frontend: Lightweight Charts 도입 + @supabase/supabase-js 패키지 추가
- [x] 60일 OHLCV 캔들스틱 차트 컴포넌트 구현 (`StockChart.tsx`)
- [x] 포트폴리오 / 관심종목 행 우측 LineChart 아이콘 토글로 차트 표시

### Step 4 — Watchlist 개인 관리
- [ ] Supabase RLS 설정: `watchlist` 테이블에 user_id 기반 Row Level Security
- [ ] frontend: Watchlist 추가/삭제 UI (StockRow에 + / - 버튼)
- [ ] backend: Lambda에서 Firestore 하드코딩 제거 → Supabase `watchlist` 테이블 동적 읽기
- [ ] tickers.py WATCHLIST 상수 → DB 조회로 교체

### Step 5 — AI 투자 비서 고도화
- [ ] 과거 데이터 기반 투자 인사이트 분석 (PostgreSQL 집계 쿼리 활용)
- [ ] 양방향 대화형 AI 챗봇 기능 추가
- [ ] 개인화된 포트폴리오 리포트 생성

## Phase 4: 인프라 고도화 (장기)
- [ ] Firebase RTDB → Supabase Realtime 이관 검토 (Realtime 성숙도 및 지연시간 < 200ms 검증 후)
- [ ] Firebase Auth → Supabase Auth 이관
- [ ] Vercel Analytics 추가 (Core Web Vitals 모니터링)
- [ ] Sentry 에러 트래킹 도입
