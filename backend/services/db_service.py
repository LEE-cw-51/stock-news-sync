import os
import json
import logging
import requests
import firebase_admin
from firebase_admin import credentials, db, firestore

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

            if firebase_json:
                logger.info("Loading Firebase creds from Environment Variable")
                cred = credentials.Certificate(json.loads(firebase_json))
            else:
                logger.info("Loading Firebase creds from Local File")
                current_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.dirname(current_dir)
                key_path = os.path.join(backend_dir, "serviceAccount.json")

                if not os.path.exists(key_path):
                    raise FileNotFoundError(f"키 파일을 찾을 수 없습니다: {key_path}")

                cred = credentials.Certificate(key_path)

            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ.get(
                    'FIREBASE_DATABASE_URL',
                    'https://stock-news-sync-default-rtdb.firebaseio.com/'
                )
            })

        self.rt = db
        self.fs = firestore.client()

        # Supabase REST API 설정 (Phase 3)
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        self._supabase_headers = {
            "apikey": self.supabase_key or "",
            "Authorization": f"Bearer {self.supabase_key or ''}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",  # UPSERT
        }

    def update_market_indices(self, path, updates):
        try:
            self.rt.reference(f"/feed/{path}").update(updates)
            logger.info("RTDB updated: /feed/%s", path)
        except Exception as e:
            logger.error("RTDB Update Error (/feed/%s): %s", path, e)
            raise

    def save_final_feed(self, data):
        try:
            # RTDB 업데이트 — update()로 기존 market_indices/key_indicators를 보존
            self.rt.reference("/feed").update(data)
            logger.info("RTDB updated: /feed")

            # Firestore 업데이트
            self.fs.collection('market_feeds').document('latest').set(data)
            logger.info("Firestore updated: market_feeds/latest")

        except Exception as e:
            logger.error("Save Final Feed Error: %s", e)
            raise

    def save_stock_history(self, records: list[dict]) -> None:
        """Supabase stock_history 테이블에 OHLCV 데이터 UPSERT.

        Args:
            records: [{"symbol": str, "date": str, "open": float,
                       "high": float, "low": float, "close": float,
                       "volume": int}, ...]
        """
        if not self.supabase_url or not self.supabase_key:
            logger.warning("SUPABASE_URL/KEY 미설정 — stock_history 저장 생략")
            return
        if not records:
            return
        try:
            url = f"{self.supabase_url}/rest/v1/stock_history"
            resp = requests.post(url, headers=self._supabase_headers, json=records, timeout=10)
            resp.raise_for_status()
            logger.info("Supabase stock_history UPSERT 완료: %d건", len(records))
        except Exception as e:
            logger.error("Supabase stock_history 저장 오류: %s", e)