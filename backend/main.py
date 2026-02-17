import sys
import os
import time
from datetime import datetime

# 1. 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from dotenv import load_dotenv
load_dotenv()

from backend.config.tickers import (
    NAME_MAP, US_CANDIDATES, KR_CANDIDATES, 
    MY_PORTFOLIO, WATCHLIST, MACRO_KEYWORDS
)
from backend.services.db_service import DBService
from backend.services.market_service import get_market_indices, get_top_volume_stocks
from backend.services.news_service import get_tavily_news
from backend.services.ai_service import generate_ai_summary

def run_sync_engine_once():
    print(f"🚀 [Start] Data Sync at {datetime.now()}")
    
    try:
        db_svc = DBService()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # [A] 지수 및 주요 지표 업데이트 (기존 유지)
        indices_config = {
            "market_indices/domestic": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
            "market_indices/global": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
            "key_indicators": { 
                "USD_KRW": "USDKRW=X", "US_10Y": "^TNX", "BTC": "BTC-USD", "Gold": "GC=F" 
            }
        }
        for path, items in indices_config.items():
            updates = get_market_indices(items)
            for key in updates: updates[key]["updated_at"] = now_str
            db_svc.update_market_indices(path, updates)

        # [B] 뉴스 데이터 수집 및 구조화
        # 프론트엔드가 요구하는 구조: { portfolio: [뉴스들...], watchlist: [뉴스들...] }
        frontend_feed = { "portfolio": [], "watchlist": [], "macro": [] }
        
        # AI 요약용 텍스트 저장소
        ai_contexts = { "macro": "", "portfolio": "", "watchlist": "" }

        # 1. 거시경제 뉴스 (Frontend는 현재 이 탭을 안 쓰지만 데이터는 확보)
        for keyword in MACRO_KEYWORDS:
            context, links = get_tavily_news(keyword)
            if context:
                ai_contexts["macro"] += f"\n[Keyword: {keyword}]\n{context}\n"
                # Tavily 데이터 변환 (url -> link)
                for item in links:
                    news_item = {
                        "title": item.get("title"),
                        "link": item.get("url"),  # <--- [중요] 프론트엔드는 link를 원함
                        "name": "Macro",          # 태그명
                        "pubDate": item.get("published_date")
                    }
                    frontend_feed["macro"].append(news_item)
            time.sleep(1)

        # 2. 종목 데이터 및 뉴스 수집
        us_stocks = get_top_volume_stocks(US_CANDIDATES, 15)
        kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 15)
        stock_data_map = {}

        for item in (us_stocks + kr_stocks):
            symbol = item['symbol']
            info = NAME_MAP.get(symbol, {"name": symbol, "sector": "기타"})
            safe_key = symbol.replace(".", "_")
            
            # 주가 정보 저장
            stock_data_map[safe_key] = {
                "symbol": symbol, "name": info['name'], "price": round(item['price'], 2),
                "change_percent": item['change_percent'], "volume": int(item['volume']),
                "sector": info.get('sector', '미분류')
            }

            # 내 종목(Portfolio/Watchlist)인 경우 뉴스 검색
            category = None
            if symbol in MY_PORTFOLIO: category = "portfolio"
            elif symbol in WATCHLIST: category = "watchlist"

            if category:
                context, links = get_tavily_news(info['name'])
                if context:
                    ai_contexts[category] += f"\n[{info['name']}]\n{context}\n"
                    
                    # [핵심] 뉴스 리스트 평탄화 (Flatten) 및 필드명 변환
                    for link_data in links:
                        news_item = {
                            "title": link_data.get("title"),
                            "link": link_data.get("url"),  # <--- [중요] url을 link로 변환
                            "name": info['name'],          # <--- [중요] 종목명 주입
                            "pubDate": link_data.get("published_date")
                        }
                        frontend_feed[category].append(news_item)
                time.sleep(1)

        # [C] AI 요약 생성
        print("🧠 Generating AI Summaries...")
        ai_summaries = {
            "macro": generate_ai_summary("글로벌 경제", ai_contexts["macro"]),
            "portfolio": generate_ai_summary("내 포트폴리오", ai_contexts["portfolio"]),
            "watchlist": generate_ai_summary("관심 종목", ai_contexts["watchlist"])
        }

        # [D] 최종 데이터 저장
        final_data = {
            "updated_at": now_str,
            "ai_summaries": ai_summaries,
            
            # [수정 완료] 프론트엔드가 원하는 { portfolio: [], watchlist: [] } 구조
            "news_feed": frontend_feed, 
            
            "stock_data": stock_data_map,
            "portfolio_list": list(MY_PORTFOLIO.keys()),
            "watchlist_list": list(WATCHLIST.keys())
        }

        db_svc.save_final_feed(final_data)
        
        # 로그 출력
        p_count = len(frontend_feed['portfolio'])
        w_count = len(frontend_feed['watchlist'])
        print(f"✅ [Success] Sync Complete. News: Port({p_count}), Watch({w_count})")

    except Exception as e:
        print(f"❌ [Error] Critical failure: {e}")
        
def lambda_handler(event, context):
    print("🚀 AWS Lambda 환경에서 동기화 엔진을 시작합니다.")
    try:
        run_sync_engine_once()
        return {
            'statusCode': 200,
            'body': '데이터 동기화 완료'
        }
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        raise e


if __name__ == "__main__":
    run_sync_engine_once()