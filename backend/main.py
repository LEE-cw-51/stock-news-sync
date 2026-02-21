import sys
import os
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info("[Start] Data Sync at %s", datetime.now())

    db_svc = DBService()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # [A] 지수 및 주요 지표 업데이트
    logger.info("[Step A] 지수 및 주요 지표 수집 시작")
    indices_config = {
        "market_indices/domestic": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
        "market_indices/global": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
        "key_indicators": {
            "USD_KRW": "USDKRW=X", "US_10Y": "^TNX", "BTC": "BTC-USD", "Gold": "GC=F"
        }
    }
    for path, items in indices_config.items():
        updates = get_market_indices(items)
        for key in updates:
            updates[key]["updated_at"] = now_str
        db_svc.update_market_indices(path, updates)

    # [B] 뉴스 데이터 수집 및 구조화
    logger.info("[Step B] 뉴스 데이터 수집 시작")
    frontend_feed = { "portfolio": [], "watchlist": [], "macro": [] }
    ai_contexts = { "macro": "", "portfolio": "", "watchlist": "" }

    # 1. 거시경제 뉴스
    for keyword in MACRO_KEYWORDS:
        context, links = get_tavily_news(keyword)
        if context:
            ai_contexts["macro"] += f"\n[Keyword: {keyword}]\n{context}\n"
            for item in links:
                news_item = {
                    "title": item.get("title"),
                    "link": item.get("url"),
                    "name": "Macro",
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

        stock_data_map[safe_key] = {
            "symbol": symbol, "name": info['name'], "price": round(item['price'], 2),
            "change_percent": item['change_percent'], "volume": int(item['volume']),
            "sector": info.get('sector', '미분류')
        }

        category = None
        if symbol in MY_PORTFOLIO: category = "portfolio"
        elif symbol in WATCHLIST: category = "watchlist"

        if category:
            context, links = get_tavily_news(info['name'])
            if context:
                ai_contexts[category] += f"\n[{info['name']}]\n{context}\n"
                for link_data in links:
                    news_item = {
                        "title": link_data.get("title"),
                        "link": link_data.get("url"),
                        "name": info['name'],
                        "pubDate": link_data.get("published_date")
                    }
                    frontend_feed[category].append(news_item)
            time.sleep(1)

    # [C] AI 요약 생성
    logger.info("[Step C] AI 요약 생성 시작")
    ai_summaries = {
        "macro":     generate_ai_summary("글로벌 경제",   ai_contexts["macro"],     category="macro"),
        "portfolio": generate_ai_summary("내 포트폴리오", ai_contexts["portfolio"], category="portfolio"),
        "watchlist": generate_ai_summary("관심 종목",    ai_contexts["watchlist"], category="watchlist"),
    }

    # [D] 최종 데이터 저장
    logger.info("[Step D] Firebase 저장 시작")
    final_data = {
        "updated_at": now_str,
        "ai_summaries": ai_summaries,
        "news_feed": frontend_feed,
        "stock_data": stock_data_map,
        "portfolio_list": list(MY_PORTFOLIO.keys()),
        "watchlist_list": list(WATCHLIST.keys())
    }

    db_svc.save_final_feed(final_data)

    p_count = len(frontend_feed['portfolio'])
    w_count = len(frontend_feed['watchlist'])
    logger.info("[Success] Sync Complete. News: Port(%d), Watch(%d)", p_count, w_count)
        
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