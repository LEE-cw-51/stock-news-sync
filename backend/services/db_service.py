import os
import json
import firebase_admin
from firebase_admin import credentials, db

class DBService:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_json = os.environ.get('FIREBASE_CONFIG')
            if firebase_json:
                cred = credentials.Certificate(json.loads(firebase_json))
            else:
                # 파일명이 serviceAccount.json인지 serviceAccountKey.json인지 확인 필요
                cred = credentials.Certificate("serviceAccount.json")
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-news-sync-default-rtdb.firebaseio.com/'
            })
        
        # [수정 핵심] self.db에 firebase_admin의 db 모듈을 할당해야 합니다.
        self.db = db

    def update_market_indices(self, path, updates):
        """시장 지수 및 거시경제 지표를 루트 하위에 각각 업데이트"""
        # path 예: "market_indices/domestic"
        self.db.reference(f"/{path}").update(updates)

    def save_final_feed(self, data):
        """뉴스 및 AI 요약 데이터를 루트에 병합 업데이트"""
        # 정확하게 루트('/') 경로를 사용하여 데이터 구조를 일치시킵니다.
        self.db.reference("/").update(data)
        print("📡 Data synced to Firebase root successfully.")