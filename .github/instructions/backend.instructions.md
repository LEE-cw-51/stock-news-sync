---
applyTo: "backend/**/*.py"
---

# Backend Instructions — Python / AWS Lambda / Supabase

## PEP 8 + Type Hints

- Follow PEP 8 for all Python code (4-space indent, snake_case).
- **Always add type hints** to function signatures (parameters and return types).

```python
def get_all_watchlist_symbols(self) -> dict: ...
def save_final_feed(self, data: dict) -> None: ...
def _build_trend_context(self, symbol: str, name: str, records: list) -> str: ...
```

- Use `dict | None` (Python 3.10+ union syntax) for optional return types.

## Service Layer Pattern

Business logic MUST be organized into `backend/services/`:

```
backend/services/
├── ai_service.py     — LLM calls (Groq/Gemini via OpenAI SDK)
├── db_service.py     — Supabase REST API read/write
├── market_service.py — yfinance market data
└── news_service.py   — Tavily + Naver News API
```

- `main.py` (`lambda_handler`) orchestrates services — it does NOT contain business logic.
- Do NOT add new top-level Python files for business logic. Add to the appropriate service or create a new file under `services/`.

## Logging — Never Use print()

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Sync started")
logger.warning("Watchlist empty — using fallback: %s", symbol)
logger.error("Supabase write failed: %s", e)
```

- Use `%s` style formatting in logger calls to defer string evaluation.
- `print()` is forbidden in production code.

## Exception Handling Rules

- **Individual ticker/API failures must NOT stop the entire run.**
- Wrap each ticker/keyword iteration in `try/except`, log a warning, and `continue`.

```python
for symbol in symbols:
    try:
        result = fetch_data(symbol)
        process(result)
    except Exception as e:
        logger.warning("Failed for %s: %s", symbol, e)
        continue
```

- Only `raise` exceptions at the `lambda_handler` top-level and in `DBService.save_final_feed()` (critical path).

## Supabase Write Pattern

- Use Supabase REST API via `requests` (the `supabase-py` SDK is too large for Lambda).
- For upsert (insert or update), use `Prefer: resolution=merge-duplicates` header.

```python
headers = {
    "apikey": self.supabase_key,
    "Authorization": f"Bearer {self.supabase_key}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}
resp = requests.post(url, json=payload, headers=headers, timeout=10)
resp.raise_for_status()
```

- All writes are upserts — never overwrite entire nodes with destructive patterns.

## Lambda Handler Pattern

```python
def lambda_handler(event, context):
    logger.info("AWS Lambda 환경에서 동기화 엔진을 시작합니다.")
    try:
        run_sync_engine_once()
        return {'statusCode': 200, 'body': '데이터 동기화 완료'}
    except Exception as e:
        logger.error("실행 실패: %s", e)
        raise
```

- `lambda_handler` MUST have exactly this signature: `(event, context)`.
- On failure, re-raise the exception so CloudWatch captures it.

## Environment Variables

```python
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    logger.error("GROQ_API_KEY is not set")
```

- Required: `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

## Lambda Package Size

- **250 MB hard limit** for the deployment package.
- Forbidden packages: `litellm`, `transformers`, `torch`, `tensorflow`, `firebase-admin` (too large).
- Use `openai` SDK with `base_url` override for both Groq and Gemini.
- After adding to `requirements.txt`, verify size locally:
  `pip install -t /tmp/test -r requirements.txt && du -sh /tmp/test`

## Ticker Key Normalization

When using ticker symbols (e.g., `BTC-USD`, `^GSPC`) as dictionary keys or JSON field names:

```python
import re
safe_key = re.sub(r'[.$#\[\]/]', '_', symbol)  # BTC-USD → BTC_USD
```

This prevents KeyError and silent data corruption when ticker symbols are used as keys in dicts or Supabase JSON payloads.
