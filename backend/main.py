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
# 2. Import
# ==========================================
import time
from datetime import datetime

# config에서 확장된 변수들을 가져옵니다.
from backend.config.tickers import (
    NAME_MAP, US_CANDIDATES, KR_CANDIDATES, 
    MY_PORTFOLIO, WATCHLIST, MACRO_KEYWORDS
)
from backend.services.db_service import DBService
from backend.services.market_service import get_market_indices, get_top_volume_stocks
from backend.services.news_service import get_google_news, get_naver_news
from backend.services.ai_service import generate_summary

def run_sync_engine_once():
    """
    전체 데이터 동기화 프로세스를 실행하는 메인 엔진
    (거시경제 + 포트폴리오 + 관심종목 통합 뉴스 요약 반영)
    """
    print(f"🚀 [Start] Data Sync Initiated at {datetime.now()}")
    
    try:
        # 1. DB 서비스 초기화
        db_svc = DBService()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # ---------------------------------------------------------
        # [A] 지수 및 주요 지표 업데이트 (기존 로직 유지)
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # [B] 뉴스 수집 및 카테고리 분류
        # ---------------------------------------------------------
        print("🔍 Collecting News & Stocks...")
        
        # 뉴스 데이터를 담을 버킷
        news_bucket = {
            "macro": [],
            "portfolio": [],
            "watchlist": []
        }

        # 1. 거시경제 뉴스 수집
        for keyword in MACRO_KEYWORDS:
            title, link = get_google_news(keyword)
            if link:
                news_bucket["macro"].append({"title": title, "link": link, "keyword": keyword})
                print(f"   🌐 [Macro] {keyword}: {title[:20]}...")

        # 2. 종목 데이터 수집 (거래량 상위)
        us_stocks = get_top_volume_stocks(US_CANDIDATES, 15) # 조금 더 많이 수집
        kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 15)
        combined_stocks = us_stocks + kr_stocks
        
        stock_data_map = {} # 주가 정보 저장용 (Symbol -> Data)

        for item in combined_stocks:
            symbol = item['symbol']
            
            # config/tickers.py의 정보 가져오기
            info = NAME_MAP.get(symbol, {"name": symbol, "sector": "기타"})
            company_name = info['name']
            
            # 주가 데이터 정리
            safe_key = symbol.replace(".", "_")
            stock_data_map[safe_key] = {
                "symbol": symbol,
                "name": company_name,
                "price": round(item['price'], 2),
                "change_percent": item['change_percent'],
                "volume": int(item['volume']),
                "sector": info.get('sector', '미분류'),
                "country": "US" if symbol in US_CANDIDATES else "KR"
            }

            # 뉴스 가져오기 (내 포트폴리오나 관심종목에 속한 경우만 분류)
            is_portfolio = symbol in MY_PORTFOLIO
            is_watchlist = symbol in WATCHLIST

            if is_portfolio or is_watchlist:
                if symbol in US_CANDIDATES:
                    title, link = get_google_news(company_name)
                else:
                    title, link = get_naver_news(company_name)
                
                news_item = {
                    "title": title, 
                    "link": link, 
                    "symbol": symbol, 
                    "name": company_name,
                    "updated_at": now_str
                }

                if is_portfolio:
                    news_bucket["portfolio"].append(news_item)
                    print(f"   💰 [My Asset] {company_name}: {title[:20]}...")
                elif is_watchlist:
                    news_bucket["watchlist"].append(news_item)
                    print(f"   👀 [Watch] {company_name}: {title[:20]}...")
            
            time.sleep(0.1) # API 부하 방지

        # ---------------------------------------------------------
        # [C] AI 요약 생성 (3단계)
        # ---------------------------------------------------------
        print("🧠 Generating AI Summaries...")
        
        ai_summaries = {
            "macro": generate_summary("글로벌 거시경제", news_bucket["macro"]),
            "portfolio": generate_summary("내 포트폴리오", news_bucket["portfolio"]),
            "watchlist": generate_summary("관심 종목", news_bucket["watchlist"])
        }

        # ---------------------------------------------------------
        # [D] 최종 데이터 구조화 및 저장
        # ---------------------------------------------------------
        final_data = {
            "updated_at": now_str,
            "ai_summaries": ai_summaries,     # AI 3줄 요약 텍스트들
            "news_feed": news_bucket,         # 카테고리별 원본 뉴스 링크들
            "stock_data": stock_data_map,     # 전체 주가 정보
            "portfolio_list": list(MY_PORTFOLIO.keys()), # 내 보유 종목 코드 리스트
            "watchlist_list": list(WATCHLIST.keys())     # 관심 종목 코드 리스트
        }

        # 기존 sync_feed 경로에 덮어쓰기 (프론트엔드에서 이 구조로 읽어야 함)
        db_svc.save_final_feed(final_data)
        
        print(f"✅ [Success] Sync Complete at {now_str}")

    except Exception as e:
        print(f"❌ [Error] Critical failure: {e}")
        raise e

if __name__ == "__main__":
    run_sync_engine_once()