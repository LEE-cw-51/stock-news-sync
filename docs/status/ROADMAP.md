# Stock-News-Sync 로드맵

## Phase 1: 뉴스 동기화 엔진 (완료)
- [x] Tavily API 기반 뉴스 수집 엔진 구축
- [x] yfinance 기반 시장 지표 및 종목 데이터 수집
- [x] Firebase(RTDB + Firestore)를 활용한 데이터 영속성 확보
- [x] 멀티 LLM(Groq, Gemini) 연동 및 429 에러 대응 로직 구현
- [x] 카테고리별 AI 모델 라우팅 (macro/portfolio/watchlist)
- [x] AWS Lambda + GitHub Actions CI/CD 배포 파이프라인

## Phase 2: 프론트엔드 대시보드 (진행 중)
- [x] 운영 안정성 강화: DevOps/SRE 에이전트 및 비서실장 중심 의사결정 체계 구축
- [x] FIREBASE_DATABASE_URL Lambda 환경변수 정식 주입 (하드코딩 폴백 제거)
- [x] CI 프론트엔드 빌드 검증 게이트 추가 (frontend-check job 병렬 실행)
- [x] Vercel 배포 파이프라인 구성 (vercel.json + GitHub Actions frontend-deploy.yml)
- [x] Firebase Auth Google 로그인 UI 연동 (헤더 로그인/로그아웃 버튼)
- [x] layout.tsx 메타데이터 수정 (title: "Stock News Sync", lang: "ko")
- [x] Next.js 16 기반 뉴스 피드 UI 구현 (컴포넌트 분리 + 탭 네비게이션)
- [x] AI 요약 구조화 표시 (호재/악재/중립 뱃지 + 불렛 파싱)
- [x] 반응형 대시보드 레이아웃 (모바일 1열 / 데스크톱 2열)
- [x] 코드 품질 개선 (ESLint 0 warnings, 타입 분리, rel="noopener", aria-label)
- [ ] 주가 시각화 차트 (히스토리 수집 인프라 구축 후 → Phase 3)
- [ ] 사용자 관심 종목(Watchlist) 개인 관리 기능 (Lambda 동적 티커 → Phase 3)

## Phase 3: AI 투자 비서 고도화
- [ ] 과거 데이터 기반 투자 인사이트 분석
- [ ] 양방향 대화형 AI 챗봇 기능 추가
- [ ] 개인화된 포트폴리오 리포트 생성
