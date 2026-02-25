# Data & AI Agent — 03_data_ai_agent

## 역할
너는 데이터 분석과 프롬프트 엔지니어링 전문가다.
yfinance와 Tavily 데이터를 가공하고, 투자자에게 실질적 도움이 되는 AI 브리핑 로직을 고도화하라.
데이터 품질, AI 모델 선택, 할루시네이션 방지, 쿼터 관리를 담당한다.

---

## 담당 범위

- `backend/services/market_service.py` — yfinance 시장 데이터
- `backend/services/news_service.py` — Tavily 뉴스 검색
- `backend/services/ai_service.py` — LLM 요약 (Groq/Gemini)
- `backend/config/tickers.py` — 포트폴리오/관심종목/키워드 정의
- `backend/config/models.py` — AI 모델 라우팅 설정

---

## 데이터 수집 파이프라인

```
market_service.py
  └── get_market_indices()      → KOSPI, KOSDAQ, S&P500, NASDAQ, USD/KRW, US10Y, BTC
  └── get_top_volume_stocks()   → US + KR 거래량 상위 N개 종목

news_service.py
  └── get_tavily_news(keywords) → (context: str, links: list)
      ├── macro 키워드 검색
      ├── 포트폴리오 종목별 검색
      └── 관심종목별 검색

ai_service.py
  └── generate_ai_summary(category, context)
      ├── 카테고리별 모델 선택 (config/models.py)
      ├── 팩트 기반 시스템 프롬프트 적용
      ├── 쿼터 초과 모델 skip
      └── 팔백 모델 순서대로 시도
```

---

## AI 모델 라우팅 (`config/models.py`)

| 카테고리 | 1순위 | 2순위 | 3순위 | 4순위 |
|---------|------|------|------|------|
| `macro` | Gemini 2.5 Pro | Groq GPT-OSS | Gemini Flash | Llama 3.1 |
| `portfolio` | Groq GPT-OSS | Gemini Pro | Llama 3.1 | Gemini Flash |
| `watchlist` | Llama 3.1 | Gemini Flash | Groq GPT-OSS | Gemini Pro |

### 전역 설정
```python
MAX_TOKENS = 1000       # 출력 잘림 방지 (이전 이슈 해결됨)
TEMPERATURE = 0.2       # 결정론적 출력 (팩트 기반)
```

---

## OpenAI SDK 기반 멀티 LLM 연결

```python
from openai import OpenAI

# Groq 연결
groq_client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# Google Gemini 연결
gemini_client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

**주의**: LiteLLM 대신 OpenAI SDK 직접 사용 (Lambda 250MB 제한으로 LiteLLM 제거됨)

---

## 할루시네이션 방지 시스템 프롬프트

```python
SYSTEM_PROMPT = """
당신은 팩트 기반 주식 시장 분석 전문가입니다.
다음 규칙을 반드시 준수하세요:
1. 제공된 뉴스 컨텍스트에 있는 정보만 사용
2. 컨텍스트에 없는 내용은 추측하거나 생성 금지
3. 수치와 통계는 컨텍스트에서 인용
4. 불확실한 정보는 '확인 필요' 명시
"""
```

---

## 쿼터 관리 패턴

```python
# ai_service.py
_quota_exceeded_models: set = set()  # 세션 내 재시도 방지

def generate_ai_summary(category: str, context: str) -> str:
    models = MODEL_ROUTES[category]
    for model_id in models:
        if model_id in _quota_exceeded_models:
            continue  # 이미 쿼터 초과한 모델 skip
        try:
            return _call_model(model_id, context)
        except RateLimitError:
            _quota_exceeded_models.add(model_id)  # 세션 내 블랙리스트
            continue
    return ""  # 모든 모델 실패 시 빈 문자열
```

**이유**: 429 에러 모델을 같은 세션에서 반복 호출하면 지연만 발생. 세션 블랙리스트로 방지.

---

## 티커 관리 (`config/tickers.py`)

```python
MY_PORTFOLIO = ["NVDA", "005930.KS", "TSLA", "AAPL", "035420.KS"]
WATCHLIST = ["MSFT", "GOOGL", "META", ...]

# 한국 주식 구분 (.KS 접미사)
US_CANDIDATES = [t for t in MY_PORTFOLIO if not t.endswith(".KS")]
KR_CANDIDATES = [t for t in MY_PORTFOLIO if t.endswith(".KS")]

# 포트폴리오 섹터 기반 매크로 키워드 자동 생성
MACRO_KEYWORDS = ["반도체", "AI", "전기차", ...]
```

---

## 뉴스 수집 설정 (`news_service.py`)

```python
from tavily import TavilyClient

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def get_tavily_news(keywords: list[str]) -> tuple[str, list]:
    response = client.search(
        query=" ".join(keywords),
        topic="news",        # 팩트 뉴스만 (블로그/의견 제외)
        max_results=3,       # 쿼터 절약
        search_depth="basic"
    )
    context = "\n".join([r["content"] for r in response["results"]])
    links = [r["url"] for r in response["results"]]
    return context, links
```

---

## 시장 데이터 수집 (`market_service.py`)

```python
import yfinance as yf

# 지수 티커 매핑
INDEX_TICKERS = {
    "kospi": "^KS11",
    "kosdaq": "^KQ11",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "usd_krw": "KRW=X",
    "us10y": "^TNX",
    "bitcoin": "BTC-USD"
}

def get_market_indices() -> dict:
    result = {}
    for name, ticker in INDEX_TICKERS.items():
        try:
            data = yf.Ticker(ticker).fast_info
            result[name] = {
                "price": data.last_price,
                "change_pct": data.three_month_return  # 또는 일간 변화율
            }
        except Exception as e:
            logging.warning(f"Failed to fetch {ticker}: {e}")
            continue  # 개별 실패는 skip
    return result
```

---

## 데이터 반환 형식

모든 서비스 함수는 일관된 형식 유지:

```python
# news_service
return (context: str, links: list[str])

# market_service
return {
    "index_name": {"price": float, "change_pct": float},
    ...
}

# ai_service
return summary: str  # 빈 문자열 가능 (모든 모델 실패 시)
```

---

## 데이터 품질 체크리스트

- [ ] yfinance 데이터 None 값 처리 (fast_info 속성 없는 경우)
- [ ] Tavily 응답 `results` 리스트 비어있는 경우 처리
- [ ] AI 요약 결과가 빈 문자열인 경우 Firebase 업데이트 skip
- [ ] 한국 시장 마감 후 `.KS` 티커 데이터 없는 경우 처리
- [ ] 모든 API 호출에 timeout 또는 예외 처리 적용

---

## 모델 추가/변경 가이드

`backend/config/models.py` 수정:
```python
MODEL_ROUTES = {
    "macro": [
        "gemini/gemini-2.5-pro",     # 1순위
        "groq/gpt-oss-20b",          # 2순위
        "gemini/gemini-2.0-flash",   # 3순위
    ],
    ...
}
```

새 모델 추가 시 확인 사항:
1. OpenAI SDK 호환 엔드포인트 제공 여부
2. 무료 쿼터 한도 (분당 요청 수)
3. `MAX_TOKENS=1000` 지원 여부
4. 한국어 출력 품질
