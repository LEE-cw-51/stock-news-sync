import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, db

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

        except Exception as e:
            logger.error("Save Final Feed Error: %s", e)
            raise