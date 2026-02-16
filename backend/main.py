import sys
import os
import time
from datetime import datetime

# ==========================================
# 1. 경로 설정 (기존 유지)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

if root_dir not in sys.path:
    sys.path.append(root_dir)

# ==========================================
# 2. Import
# ==========================================
from dotenv import load_dotenv
load_dotenv() # 환경변수 로드

# 기존 설정 파일 가져오기
from backend.config.tickers import (
    NAME_MAP, US_CANDIDATES, KR_CANDIDATES, 
    MY_PORTFOLIO, WATCHLIST, MACRO_KEYWORDS
)
from backend.services.db_service import DBService
from backend.services.market_service import get_market_indices, get_top_volume_stocks

# [변경] 새로운 서비스로 교체 (Tavily, Groq)
from backend.services.news_service import get_tavily_news
from backend.services.ai_service import generate_ai_summary

def run_sync_engine_once():
    """
    통합 엔진: 시장 지수 + 주가 데이터 + RAG 기반 뉴스 요약
    """
    print(f"🚀 [Start] Data Sync Initiated at {datetime.now()}")
    
    try:
        # 1. DB 서비스 초기화
        db_svc = DBService()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # ---------------------------------------------------------
        # [A] 지수 및 주요 지표 업데이트 (기존 로직 100% 유지)
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
        # [B] 뉴스 수집 및 주가 데이터 처리 (Tavily 적용)
        # ---------------------------------------------------------
        print("🔍 Collecting News (Tavily) & Stocks...")
        
        # 프론트엔드에 보여줄 링크 모음
        news_bucket = { "macro": [], "portfolio": [], "watchlist": [] }
        
        # AI에게 먹여줄 텍스트 모음 (Context Accumulator)
        ai_contexts = { "macro": "", "portfolio": "", "watchlist": "" }

        # 1. 거시경제 뉴스 (Tavily)
        for keyword in MACRO_KEYWORDS:
            # [변경] get_google_news -> get_tavily_news
            context, links = get_tavily_news(keyword)
            if context:
                ai_contexts["macro"] += f"\n[Keyword: {keyword}]\n{context}\n"
                news_bucket["macro"].extend(links)
                print(f"   🌐 [Macro] {keyword}: 수집 완료")
            time.sleep(1) # API 부하 조절

        # 2. 종목 데이터 수집 (기존 로직 유지 + Tavily 통합)
        us_stocks = get_top_volume_stocks(US_CANDIDATES, 15)
        kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 15)
        combined_stocks = us_stocks + kr_stocks
        
        stock_data_map = {}

        for item in combined_stocks:
            symbol = item['symbol']
            info = NAME_MAP.get(symbol, {"name": symbol, "sector": "기타"})
            company_name = info['name']
            
            # 주가 데이터 정리 (기존 유지)
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

            # [변경] 내 종목인 경우 Tavily 검색 실행
            is_portfolio = symbol in MY_PORTFOLIO
            is_watchlist = symbol in WATCHLIST

            if is_portfolio or is_watchlist:
                print(f"   🔎 Checking News for {company_name}...")
                
                # Tavily로 본문과 링크 가져오기
                context, links = get_tavily_news(company_name)
                
                news_item = {
                    "symbol": symbol, 
                    "name": company_name,
                    "links": links, # 여러 개의 링크가 들어감
                    "updated_at": now_str
                }

                if is_portfolio:
                    news_bucket["portfolio"].append(news_item)
                    ai_contexts["portfolio"] += f"\n[{company_name}]\n{context}\n"
                elif is_watchlist:
                    news_bucket["watchlist"].append(news_item)
                    ai_contexts["watchlist"] += f"\n[{company_name}]\n{context}\n"
                
                time.sleep(1) # Tavily API 속도 조절

        # ---------------------------------------------------------
        # [C] AI 요약 생성 (Groq RAG 적용)
        # ---------------------------------------------------------
        print("🧠 Generating AI Summaries (Groq RAG)...")
        
        # [변경] 단순 요약 -> 본문 기반 심층 요약
        # 모아둔 context 텍스트를 한 번에 보내서 카테고리별 브리핑 생성
        ai_summaries = {
            "macro": generate_ai_summary("글로벌 거시경제", ai_contexts["macro"]),
            "portfolio": generate_ai_summary("내 포트폴리오 종합", ai_contexts["portfolio"]),
            "watchlist": generate_ai_summary("관심 종목 종합", ai_contexts["watchlist"])
        }

        # ---------------------------------------------------------
        # [D] 최종 데이터 구조화 및 저장 (기존 유지)
        # ---------------------------------------------------------
        final_data = {
            "updated_at": now_str,
            "ai_summaries": ai_summaries,     # Groq이 만든 3줄 요약
            "news_feed": news_bucket,         # Tavily가 찾은 링크들
            "stock_data": stock_data_map,     # 야후 파이낸스 주가 정보
            "portfolio_list": list(MY_PORTFOLIO.keys()),
            "watchlist_list": list(WATCHLIST.keys())
        }

        db_svc.save_final_feed(final_data)
        
        print(f"✅ [Success] Sync Complete at {now_str}")

    except Exception as e:
        print(f"❌ [Error] Critical failure: {e}")
        # raise e # 배포 시에는 주석 해제 권장

if __name__ == "__main__":
    run_sync_engine_once()