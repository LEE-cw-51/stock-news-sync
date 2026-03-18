# CLAUDE.md — stock-news-sync

> 이 파일은 Claude Code가 세션마다 자동으로 읽는 프로젝트 컨텍스트 파일입니다.
> 상세 레퍼런스는 `docs/reference/` 하위 파일을 참조하세요.

---

## 프로젝트 개요

**stock-news-sync**는 한국어/영어 AI 투자 브리핑 플랫폼입니다.
- 주식 시장 데이터(yfinance) + 뉴스(Tavily API) 수집
- Groq / Google Gemini LLM으로 카테고리별 AI 요약 생성
- Firebase Realtime Database 저장 → Next.js 대시보드 실시간 표시
- AWS Lambda 자동 실행 (GitHub Actions CI/CD)

---

## 기술 스택

| 영역 | 주요 기술 |
|------|---------|
| Frontend | Next.js 16.1.5 (App Router), React 19, TypeScript 5, Tailwind CSS v4 |
| Auth / RT DB | Firebase Auth (Google Sign-In) + Firebase Realtime Database |
| Chart / History | lightweight-charts + Supabase PostgreSQL (stock_history) |
| Backend | Python 3.11, AWS Lambda (ap-northeast-2) |
| AI/LLM | Groq + Google Gemini (OpenAI SDK, base_url 변경) |
| Data | yfinance (시장 데이터), Tavily API (뉴스) |
| CI/CD | GitHub Actions → S3 → Lambda / Vercel (프론트) |

> 패키지 크기 제한: Lambda 250MB — LiteLLM 등 대형 패키지 사용 금지

---

## 디렉터리 구조 (최상위)

```
stock-news-sync/
├── CLAUDE.md               # 이 파일
├── .claude/agents/         # 01~04번 에이전트 프롬프트
├── docs/
│   ├── operations/         # AGENT_DIRECTORY.md, PLAYBOOK.md
│   ├── reference/          # PROJECT_STRUCTURE.md, ENV_VARS.md, CONVENTIONS.md, DATA_SCHEMA.md
│   └── status/             # ROADMAP.md, PROGRESS.log, HANDOFF.md
├── backend/                # Python Lambda 핸들러 + services/
└── frontend/               # Next.js App Router
```

> 상세 트리: `docs/reference/PROJECT_STRUCTURE.md`

---

## 환경 변수 (키 목록)

- **backend/.env**: `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `FIREBASE_SERVICE_ACCOUNT`, `FIREBASE_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- **frontend/.env.local**: `NEXT_PUBLIC_FIREBASE_*` (7개), `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

> 상세 값 / GitHub Secrets 목록: `docs/reference/ENV_VARS.md`

---

## 행동 수칙 (Claude Code 필수 준수)

1. **파일 수정 전 반드시 읽기**: 코드를 이해한 후 수정. 읽지 않고 추측으로 수정 금지.
2. **API 키 절대 하드코딩 금지**: `.env` 파일 또는 환경변수 경유. 코드/커밋에 포함 금지.
3. **Lambda 배포는 GitHub Actions 경유만**: 직접 `aws lambda update-function-code` 실행 금지.
4. **Firebase 데이터 구조 변경 전 `db_service.py` 검토**: RTDB 경로(`/feed/`) 일관성 유지 필수.
5. **패키지 추가 시 250MB 제한 확인**: `requirements.txt`에 추가 전 패키지 크기 확인. LiteLLM 금지.
6. **보안 취약점 발견 즉시 수정 후 보고**: XSS, key 노출, injection 등 발견 시 수정 우선.
7. **과도한 추상화 금지**: 현재 요구사항에 필요한 최소한의 코드만 작성.
8. **테스트 없이 운영 데이터 구조 변경 금지**: `test_run.py`로 로컬 검증 후 커밋.
9. **중앙 보고 체계 준수**: 01~03번 에이전트는 반드시 04번(Tech Lead PM)을 경유하여 보고한다.
10. **Git 커밋 규칙 엄수**: 01번·03번 에이전트는 직접 커밋 금지. 02번이 04번 QA 후 커밋 수행.
    단, 문서 파일(.md)만 수정한 경우 04번(Tech Lead PM)이 직접 커밋 가능.
    커밋 메시지: `[Feat]` / `[Fix]` / `[Docs]` / `[Style]` / `[Refactor]` / `[Test]` / `[Chore]`

---

## 자율 작업 및 보고 규칙

1. **자율 검증**: 수정 후 `npm run lint`(프론트) / `python test_run.py`(백엔드) 직접 실행.
2. **문서 동기화**: 의미 있는 작업 완료 시 `docs/status/PROGRESS.log` 업데이트.
3. **문맥 유지**: 기술 변화(라이브러리 추가, 구조 변경) 발생 시 이 파일(`CLAUDE.md`) 갱신.
4. **중앙 보고**: 04번(Tech Lead PM)이 작업 결과를 취합 · 우선순위 매겨 최종 보고.

---

## 자주 쓰는 명령어

```bash
# Frontend
cd frontend && npm run dev        # 개발 서버 http://localhost:3000
cd frontend && npm run lint       # ESLint 검사

# Backend
cd backend && python test_run.py  # 로컬 테스트
cd backend && python main.py      # Lambda 핸들러 직접 실행

# 배포 (CI/CD 자동)
git push origin main
```

---

## 내장 에이전트 타입 활용 가이드

| 타입 | 언제 사용 | 특성 |
|------|---------|------|
| `Explore` | 코드 탐색, 패턴 검색 | 읽기 전용, 빠름 |
| `Plan` | 구현 계획 수립, 아키텍처 설계 | 읽기 전용, 설계 특화 |
| `general-purpose` | 복잡한 멀티파일 작업 | 모든 도구 접근 가능 |

**04번(Tech Lead PM) QA 활용 예시:**
- Firebase RTDB 경로 일관성 검사 → `Explore` 서브에이전트 사용
- Phase N 기능 구현 계획 → `Plan` 서브에이전트 사용

**02번(Backend) 복잡 작업 활용 예시:**
- 수정 전 코드 의존성 파악 → `Explore` 먼저 실행 후 직접 수정

**01번/03번(워크트리 격리 환경):**
- 새 기능 구현 전 기존 패턴 탐색 → 자신의 워크트리 내에서 `Explore` 사용

> 내장 에이전트는 모든 에이전트(01~04번)의 `Agent` 도구를 통해 호출 가능.

---

## 참조 문서

| 문서 | 내용 |
|------|------|
| `docs/reference/PROJECT_STRUCTURE.md` | 전체 디렉터리 트리 |
| `docs/reference/ENV_VARS.md` | 환경 변수 상세 목록 |
| `docs/reference/CONVENTIONS.md` | 코딩 컨벤션 + 커밋 메시지 규칙 |
| `docs/reference/DATA_SCHEMA.md` | Firebase/Supabase 스키마 + AI 모델 라우팅 |
| `docs/operations/PLAYBOOK.md` | 에이전트 협업 SOP |
| `docs/status/ROADMAP.md` | Phase별 진행 현황 |
