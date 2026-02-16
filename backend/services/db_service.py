import os
import json
import firebase_admin
from firebase_admin import credentials, db, firestore

class DBService:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
            
            if firebase_json:
                print("🔑 Loading Firebase creds from Environment Variable...")
                cred = credentials.Certificate(json.loads(firebase_json))
            else:
                print("🔑 Loading Firebase creds from Local File...")
                
                # 현재 파일 기준 상위 폴더(backend) 경로 계산
                current_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.dirname(current_dir)
                
                # [수정] 파일 이름을 요청하신 대로 serviceAccount.json으로 설정
                key_path = os.path.join(backend_dir, "serviceAccount.json")
                
                if not os.path.exists(key_path):
                    raise FileNotFoundError(f"❌ 키 파일을 찾을 수 없습니다: {key_path}")
                
                cred = credentials.Certificate(key_path)

            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-news-sync-default-rtdb.firebaseio.com/'
            })

        self.rt = db
        self.fs = firestore.client()

    def update_market_indices(self, path, updates):
        try:
            self.rt.reference(f"/{path}").update(updates)
            print(f"📡 RTDB updated: {path}")
        except Exception as e:
            print(f"❌ RTDB Update Error ({path}): {e}")

    def save_final_feed(self, data):
        try:
            # RTDB 업데이트
            self.rt.reference("/").update(data)
            print("📡 RTDB updated: / (Full Feed)")

            # Firestore 업데이트
            self.fs.collection('market_feeds').document('latest').set(data)
            print("📁 Firestore updated: market_feeds/latest")
            
        except Exception as e:
            print(f"❌ Save Final Feed Error: {e}")