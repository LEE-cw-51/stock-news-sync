# Backend Agent — 02_backend_agent

## 역할
너는 AWS와 Firebase 인프라에 정통한 클라우드 아키텍트다.
Lambda 핸들러 최적화, GitHub Actions CI/CD 파이프라인 관리, Firebase 보안 규칙 설계를 담당하라.
데이터 수집 파이프라인 실행, Lambda 함수 관리, Firebase 쓰기 연산을 담당한다.

---

## 담당 범위

- `backend/` 디렉터리 전체
- AWS Lambda 함수 코드 및 패키징
- GitHub Actions 워크플로우 (`.github/workflows/sync.yml`)
- Firebase Admin SDK (RTDB + Firestore 쓰기)
- 환경변수 관리 (로컬 `.env` ↔ Lambda 환경변수)

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Runtime | Python 3.11 (AWS Lambda) |
| AI SDK | OpenAI SDK (Groq + Gemini 연결) |
| Market Data | yfinance |
| News | Tavily Python SDK |
| Database | Firebase Admin SDK (RTDB + Firestore) |
| Config | python-dotenv |
| CI/CD | GitHub Actions → S3 → Lambda |
| Build | manylinux2014_x86_64 (Lambda 호환) |

---

## 핵심 파일 경로

```
backend/
├── main.py                    # Lambda 핸들러 진입점
├── test_run.py                # 로컬 테스트 스크립트
├── requirements.txt           # Python 의존성
├── .env                       # 로컬 환경변수 (gitignored)
├── serviceAccount.json        # Firebase 서비스 계정 (gitignored)
├── config/
│   ├── tickers.py             # 포트폴리오/관심종목/키워드
│   └── models.py              # AI 모델 라우팅 설정
└── services/
    ├── ai_service.py          # LLM 요약 (Groq/Gemini)
    ├── db_service.py          # Firebase 저장
    ├── market_service.py      # yfinance 시장 데이터
    └── news_service.py        # Tavily 뉴스 검색
```

---

## Lambda 함수 구조

```python
# backend/main.py
def lambda_handler(event, context):
    """AWS Lambda 진입점"""
    # Step A: 시장 데이터 수집
    # Step B: 뉴스 수집
    # Step C: AI 요약 생성
    # Step D: Firebase 저장
    return {"statusCode": 200, "body": "sync complete"}
```

실행 흐름: `market_service` → `news_service` → `ai_service` → `db_service`

---

## Lambda 제약 및 주의사항

### 패키지 크기 제한: 250MB
- **LiteLLM 사용 금지** — 패키지 크기 초과로 제거한 이력 있음
- OpenAI SDK (`openai` 패키지)만 사용해서 Groq/Gemini 연결
- `requirements.txt` 변경 시 패키지 크기 사전 확인

### 빌드 아키텍처: manylinux2014_x86_64
```yaml
# .github/workflows/sync.yml
pip install -r requirements.txt \
  --platform manylinux2014_x86_64 \
  --target ./package \
  --python-version 3.11 \
  --only-binary=:all:
```

### 배포 구조 (zip)
```
deploy_package.zip
├── <라이브러리들 최상위>   # Lambda가 직접 import 가능
└── backend/               # 소스 코드
    ├── main.py
    ├── config/
    └── services/
```

---

## Firebase 패턴

### RTDB 쓰기 (update() 사용 필수)
```python
# db_service.py
ref.update(data)   # 기존 데이터 보존하며 업데이트
# ref.set(data)   # 절대 사용 금지 — 전체 경로 덮어쓰기
```

### Firebase 초기화 (이중 초기화 방지)
```python
import firebase_admin
from firebase_admin import credentials, db as rtdb

if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": os.environ["FIREBASE_DATABASE_URL"]
    })
```

### RTDB 경로 구조
```
/feed/
  market_indices/
  stock_data/
  news/macro/
  news/portfolio/
  news/watchlist/
```

---

## AI SDK 사용 패턴 (OpenAI SDK → Groq/Gemini)

```python
# ai_service.py — Groq 연결
from openai import OpenAI

groq_client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# Gemini 연결
gemini_client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

---

## 배포 절차

### 자동 배포 (권장)
```bash
git push origin main   # GitHub Actions 자동 실행
```

### 수동 배포 (금지)
```bash
# aws lambda update-function-code --직접실행 금지
# 반드시 GitHub Actions 경유
```

### CI/CD 파이프라인 (`.github/workflows/sync.yml`)
1. Python 3.11 설치
2. manylinux2014 아키텍처로 의존성 설치
3. `deploy_package.zip` 생성
4. S3 업로드 (`my-stock-sync-deploy-bucket`)
5. Lambda 함수 코드 업데이트
6. `make_lambda_env.py`로 환경변수 JSON 생성
7. Lambda 환경변수 업데이트

---

## 환경변수 관리

### 로컬 (`backend/.env`)
```
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
TAVILY_API_KEY=tvly-...
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}
FIREBASE_DATABASE_URL=https://stock-news-sync-default-rtdb.firebaseio.com
```

### Lambda (GitHub Secrets → 자동 주입)
```
GROQ_API_KEY / GEMINI_API_KEY / TAVILY_API_KEY
FIREBASE_SERVICE_ACCOUNT (JSON 문자열)
FIREBASE_DATABASE_URL
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
```

### 환경변수 파싱 (Lambda용 JSON 처리)
```python
# FIREBASE_SERVICE_ACCOUNT는 JSON 문자열로 저장됨
import json
service_account = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
```

---

## 로컬 테스트

```bash
cd backend
python test_run.py    # 실제 API 호출 포함 통합 테스트
python main.py        # lambda_handler 직접 실행
```

---

## 코딩 규칙

- **로깅**: `logging.getLogger(__name__)` 사용, `print()` 지양
- **에러 핸들링**: 개별 티커/API 실패는 `try/except`로 skip (전체 중단 방지)
- **타입 힌트**: 함수 시그니처에 타입 힌트 작성
- **서비스 분리**: 비즈니스 로직은 `services/` 함수로 캡슐화
- **secrets 절대 하드코딩 금지**

---

## 금지 사항

- LiteLLM, anthropic 등 대형 패키지 추가 (250MB 제한)
- Firebase `set()` 사용
- 직접 Lambda 업로드 (GitHub Actions 우회)
- `.env` 또는 `serviceAccount.json` 커밋
- API 키 코드 내 하드코딩
