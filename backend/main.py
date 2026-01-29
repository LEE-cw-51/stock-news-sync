import sys
import os

# ==========================================
# 1. [핵심] 프로젝트 루트 경로 강제 등록
# ==========================================
# 현재 파일(main.py)의 위치: .../stock-news-sync/backend/main.py
# 우리가 필요한 루트 경로:   .../stock-news-sync/
current_dir = os.path.dirname(os.path.abspath(__file__)) # backend 폴더
root_dir = os.path.dirname(current_dir)                  # stock-news-sync 폴더

# 시스템 경로에 루트가 없으면 추가 (이제 'backend' 패키지를 인식할 수 있음)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# ==========================================
# 2. Import (이제 'backend.'으로 시작 가능)
# ==========================================
import time
from datetime import datetime
from backend.config.tickers import NAME_MAP, US_CANDIDATES, KR_CANDIDATES
from backend.services.db_service import DBService
from backend.services.market_service import get_market_indices, get_top_volume_stocks
from backend.services.news_service import get_google_news, get_naver_news

def run_sync_engine_once():
    """
    전체 데이터 동기화 프로세스를 실행하는 메인 엔진
    """
    print(f"🚀 [Start] Data Sync Initiated at {datetime.now()}")
    
    try:
        # 1. DB 서비스 초기화
        db_svc = DBService()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 2. [A] 지수 및 주요 지표 업데이트
        indices_config = {
            "market_indices/domestic": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
            "market_indices/global": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
            "key_indicators": { 
                "USD_KRW": "USDKRW=X", 
                "US_10Y": "^TNX", 
                "BTC": "BTC-USD", 
                "Gold": "GC=F" 
            }
        }

        for path, items in indices_config.items():
            print(f"📊 Updating {path}...")
            updates = get_market_indices(items)
            for key in updates:
                updates[key]["updated_at"] = now_str
            db_svc.update_market_indices(path, updates)

        # 3. [B] 종목별 주가 및 뉴스 업데이트
        print("🔍 Fetching top volume stocks...")
        us_stocks = get_top_volume_stocks(US_CANDIDATES, 10)
        kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 10)
        
        final_feed = {}
        combined_list = us_stocks + kr_stocks

        for item in combined_list:
            symbol = item['symbol']
            # tickers.py의 상세 정보 가져오기
            info = NAME_MAP.get(symbol, {"name": symbol, "sector": "기타"})
            company_name = info['name']
            
            # 국가 판별 및 뉴스 소스 선택
            is_us = symbol in US_CANDIDATES
            if is_us:
                news_title, news_url = get_google_news(company_name)
            else:
                news_title, news_url = get_naver_news(company_name)
            
            # Firebase 키 안전 문자열 처리
            safe_key = symbol.replace(".", "_")
            
            final_feed[safe_key] = {
                "company_name": company_name,
                "sector": info.get('sector', '미분류'),
                "price": round(item['price'], 2),
                "volume": int(item['volume']),
                "change_percent": item['change_percent'],
                "news_title": news_title,
                "news_url": news_url,
                "country": "US" if is_us else "KR",
                "updated_at": now_str
            }
            print(f"   👉 [{'US' if is_us else 'KR'}] {company_name}: {news_title[:25]}...")
            time.sleep(0.1) # API 과부하 방지

        # 4. 최종 데이터 저장
        db_svc.save_final_feed(final_feed)
        print(f"✅ [Success] Sync Complete at {now_str}")

    except Exception as e:
        print(f"❌ [Error] Critical failure: {e}")
        raise e

if __name__ == "__main__":
    run_sync_engine_once()