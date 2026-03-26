import sys
import os
import re
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
    MY_PORTFOLIO, WATCHLIST, MACRO_KEYWORDS, KR_MACRO_KEYWORDS
)
from backend.services.db_service import DBService
from backend.services.market_service import get_market_indices, get_top_volume_stocks, get_stock_history  # get_stock_history: AI 추세 컨텍스트용
from backend.services.news_service import get_tavily_news, get_naver_news, get_foreign_news, get_korean_news
from backend.services.ai_service import generate_ai_summary

def _build_trend_context(symbol: str, name: str, records: list) -> str:
    """60일 주가 히스토리에서 AI 프롬프트용 추세 컨텍스트 문자열 생성."""
    if not records:
        return ""
    closes = [r["close"] for r in records if r.get("close") is not None]
    if len(closes) < 10:
        return ""
    latest = closes[-1]
    prev_5 = closes[-5] if len(closes) >= 5 else closes[0]
    prev_30 = closes[-30] if len(closes) >= 30 else closes[0]
    ret_5d = (latest - prev_5) / prev_5 * 100
    ret_30d = (latest - prev_30) / prev_30 * 100
    high_60d = max(closes)
    low_60d = min(closes)
    return (
        f"[{name} 주가 추세 (60일 히스토리 기반)]\n"
        f"- 현재가: {latest:.2f}, 5일 수익률: {ret_5d:+.2f}%, 30일 수익률: {ret_30d:+.2f}%\n"
        f"- 60일 고가: {high_60d:.2f}, 저가: {low_60d:.2f}\n"
    )


def run_sync_engine_once():
    logger.info("[Start] Data Sync at %s", datetime.now())

    db_svc = DBService()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 동적 Watchlist 로드 (Supabase DB)
    # Supabase 미설정이거나 DB가 비어있으면 tickers.py 폴백 사용
    dynamic_watchlist = db_svc.get_all_watchlist_symbols()
    active_watchlist = dynamic_watchlist if dynamic_watchlist else WATCHLIST
    # NAME_MAP 업데이트: 동적 watchlist 심볼 포함
    active_name_map = {**NAME_MAP, **active_watchlist}

    # [A] 지수 및 주요 지표 업데이트
    logger.info("[Step A] 지수 및 주요 지표 수집 시작")
    indices_config = {
        "market_indices/domestic": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
        "market_indices/global": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
        "key_indicators": {
            "USD_KRW": "USDKRW=X", "US_10Y": "^TNX", "BTC": "BTC-USD", "Gold": "GC=F"
        }
    }
    collected_indices = {"market_indices": {"domestic": {}, "global": {}}, "key_indicators": {}}
    for path, items in indices_config.items():
        updates = get_market_indices(items)
        for key in updates:
            updates[key]["updated_at"] = now_str
        db_svc.update_market_indices(path, updates)
        # Supabase final_data에 포함하기 위해 누적
        if path == "market_indices/domestic":
            collected_indices["market_indices"]["domestic"] = updates
        elif path == "market_indices/global":
            collected_indices["market_indices"]["global"] = updates
        elif path == "key_indicators":
            collected_indices["key_indicators"] = updates

    # [B] 뉴스 데이터 수집 및 구조화
    logger.info("[Step B] 뉴스 데이터 수집 시작")
    frontend_feed = { "portfolio": [], "watchlist": [], "macro": [] }
    ai_contexts = { "macro": "", "portfolio": "", "watchlist": "" }

    # 1. 거시경제 뉴스 (영문 — Tavily)
    for keyword in MACRO_KEYWORDS:
        try:  # [P4 Fix] 개별 키워드 뉴스 수집 실패 시 전체 중단 방지 (종목 뉴스와 동일 패턴)
            context, links = get_foreign_news(keyword)
            if context:
                ai_contexts["macro"] += f"\n[Keyword: {keyword}]\n{context}\n"
                for item in links:
                    news_item = {
                        "title": item.get("title"),
                        "link": item.get("url"),
                        "name": "Macro",
                        "pubDate": item.get("date")  # [P1 Fix] news_service.py 반환 key는 "date"
                    }
                    frontend_feed["macro"].append(news_item)
            time.sleep(1)
        except Exception as e:
            logger.warning("매크로 뉴스 수집 실패 (%s): %s", keyword, e)
            continue

    # 1-2. 한국 거시경제 뉴스 (한국어 — Naver)
    for keyword in KR_MACRO_KEYWORDS:
        try:
            context, links = get_korean_news(keyword)
            if context:
                ai_contexts["macro"] += f"\n[한국 거시: {keyword}]\n{context}\n"
                for item in links:
                    news_item = {
                        "title": item.get("title"),
                        "link": item.get("url"),
                        "name": "한국 거시경제",
                        "pubDate": item.get("date")
                    }
                    frontend_feed["macro"].append(news_item)
            time.sleep(1)
        except Exception as e:
            logger.warning("한국 거시뉴스 수집 실패 (%s): %s", keyword, e)
            continue

    # 2. 종목 데이터 및 뉴스 수집
    us_stocks = get_top_volume_stocks(US_CANDIDATES, 15)
    kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 15)
    stock_data_map = {}

    for item in (us_stocks + kr_stocks):
        symbol = item['symbol']
        info = active_name_map.get(symbol, {"name": symbol, "sector": "기타"})
        # [P3 Fix] Firebase 경로 금지 문자(. $ # [ ] /) 일괄 치환
        safe_key = re.sub(r'[.$#\[\]/]', '_', symbol)

        stock_data_map[safe_key] = {
            "symbol": symbol, "name": info['name'], "price": round(item['price'], 2),
            "change_percent": item['change_percent'], "volume": int(item['volume']),
            "sector": info.get('sector', '미분류')
        }

        category = None
        if symbol in MY_PORTFOLIO: category = "portfolio"
        elif symbol in active_watchlist: category = "watchlist"

        if category:
            try:  # [P4 Fix] 개별 종목 뉴스 수집 실패 시 전체 중단 방지
                # KS 종목은 Naver News API로 한국어 뉴스 수집, 그 외는 Tavily 사용
                kr_name = info.get("kr_name")
                if symbol.endswith(".KS") and kr_name:
                    context, links = get_korean_news(kr_name)
                else:
                    context, links = get_foreign_news(info['name'], symbol=symbol)
                if context:
                    ai_contexts[category] += f"\n[{info['name']}]\n{context}\n"
                    for link_data in links:
                        news_item = {
                            "title": link_data.get("title"),
                            "link": link_data.get("url"),
                            "name": info['name'],
                            "pubDate": link_data.get("date")  # [P1 Fix] news_service.py 반환 key는 "date"
                        }
                        frontend_feed[category].append(news_item)
                time.sleep(1)
            except Exception as e:
                logger.warning("종목 뉴스 수집 실패 (%s): %s", symbol, e)
                continue

    # [B.5] 60일 주가 히스토리 수집 → AI 추세 컨텍스트 주입
    logger.info("[Step B.5] 주가 추세 컨텍스트 수집 시작")
    all_symbols = list(MY_PORTFOLIO.keys()) + list(active_watchlist.keys())
    for symbol in all_symbols:
        cat = "portfolio" if symbol in MY_PORTFOLIO else "watchlist"
        info = active_name_map.get(symbol, {"name": symbol})
        records = get_stock_history(symbol)
        trend_text = _build_trend_context(symbol, info['name'], records)
        if trend_text:
            ai_contexts[cat] += trend_text

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
        "market_indices": collected_indices["market_indices"],
        "key_indicators": collected_indices["key_indicators"],
        "ai_summaries": ai_summaries,
        "news_feed": frontend_feed,
        "portfolio_list": list(MY_PORTFOLIO.keys()),
        "watchlist_list": list(active_watchlist.keys())
    }
    # Firebase RTDB에서 빈 dict는 null로 처리되어 기존 데이터를 삭제함 → 데이터 있을 때만 포함
    if stock_data_map:
        final_data["stock_data"] = stock_data_map
    else:
        logger.warning("[Step D] stock_data 비어있음 — 기존 Firebase 데이터 보존")

    db_svc.save_final_feed(final_data)

    p_count = len(frontend_feed['portfolio'])
    w_count = len(frontend_feed['watchlist'])
    logger.info("[Success] Sync Complete. News: Port(%d), Watch(%d)", p_count, w_count)

def lambda_handler(event, context):
    logger.info("AWS Lambda 환경에서 동기화 엔진을 시작합니다.")  # [P6 Fix] print → logging
    try:
        run_sync_engine_once()
        return {
            'statusCode': 200,
            'body': '데이터 동기화 완료'
        }
    except Exception as e:
        logger.error("실행 실패: %s", e)  # [P6 Fix] print → logging
        raise e


if __name__ == "__main__":
    run_sync_engine_once()
