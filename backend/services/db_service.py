import os
import math
import numbers
import logging
from typing import Any
import requests

logger = logging.getLogger(__name__)


def _sanitize_floats(obj: Any) -> Any:
    """NaN/Inf float 값을 0으로 치환 (JSON 직렬화 오류 방지).

    yfinance/pandas 경유 numpy.float64 등 float 서브타입도 커버.
    - bool: int 서브클래스이므로 먼저 제외
    - numbers.Integral (int, numpy.int64 등): NaN/Inf 불가 → 그대로 반환
    - numbers.Real (float, numpy.float64 등): NaN/Inf 체크 후 0.0으로 치환
    """
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, numbers.Integral):
        return int(obj)  # numpy.int64 등 → 표준 int 변환 (JSON 직렬화 보장)
    if isinstance(obj, numbers.Real):
        try:
            f = float(obj)
            return 0.0 if (math.isnan(f) or math.isinf(f)) else f
        except (ValueError, OverflowError):
            return 0.0
    if isinstance(obj, dict):
        return {k: _sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_floats(v) for v in obj]
    return obj


class DBService:
    def __init__(self):
        # Supabase REST API 설정
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    def update_market_indices(self, path: str, updates: dict) -> None:
        # save_final_feed()가 Step D에서 전체 데이터를 UPSERT하므로 no-op 처리
        if not updates:
            logger.warning("update_market_indices skip (빈 updates): %s", path)
        else:
            logger.info("update_market_indices deferred to save_final_feed: %s", path)

    def save_final_feed(self, data: dict) -> None:
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("SUPABASE_URL 또는 SUPABASE_SERVICE_ROLE_KEY 미설정")
        url = f"{self.supabase_url}/rest/v1/feed"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        payload = _sanitize_floats({"id": 1, **data})
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            logger.info("feed saved to Supabase")
        except Exception as e:
            logger.error("Save Final Feed Error: %s", e)
            raise

    def get_all_watchlist_symbols(self) -> dict:
        """Supabase watchlist 테이블에서 전체 유저의 심볼 집계.

        Lambda service_role로 RLS 우회. unique 심볼 기준으로 반환.

        Returns:
            {symbol: {"name": str, "sector": str}} 형태의 dict.
            Supabase 미설정 또는 오류 시 빈 dict 반환 (폴백 허용).
        """
        if not self.supabase_url or not self.supabase_key:
            logger.warning("SUPABASE_URL/KEY 미설정 — watchlist 조회 생략")
            return {}
        try:
            url = f"{self.supabase_url}/rest/v1/watchlist"
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
            }
            params = {"select": "symbol,name,sector"}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            rows = resp.json()
            # unique symbol 기준 집계 (중복 심볼은 첫 번째 항목 사용)
            result: dict = {}
            for row in rows:
                symbol = row.get("symbol", "")
                if symbol and symbol not in result:
                    result[symbol] = {
                        "name": row.get("name") or symbol,
                        "sector": row.get("sector") or "기타",
                    }
            logger.info("Supabase watchlist 조회 완료: %d개 unique 심볼", len(result))
            return result
        except Exception as e:
            logger.error("Supabase watchlist 조회 오류: %s", e)
            return {}

