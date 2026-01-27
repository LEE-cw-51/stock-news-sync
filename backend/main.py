import os
import json
import firebase_admin
from firebase_admin import credentials, db
import yfinance as yf
import time
import feedparser
import requests
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 설정 및 API 키 (환경 변수 우선)
# ==========================================

# [Naver API] GitHub Secrets에서 가져오거나, 없으면 로컬 테스트용 값 사용
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "zhHWNVx4FqeKbc2IbQoM")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "S6ay2XGyv3")

# [Firebase 인증]
# GitHub Actions에서는 환경 변수(FIREBASE_CONFIG)를 사용하고,
# 로컬 컴퓨터에서는 파일(serviceAccount.json)을 사용하도록 분기 처리
if not firebase_admin._apps:
    firebase_json = os.environ.get('FIREBASE_CONFIG')
    
    if firebase_json:
        # GitHub Actions 환경: JSON 문자열을 파싱해서 사용
        print("🔒 Using Firebase Config from Environment Variable")
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # 로컬 개발 환경: 파일 사용
        print("📂 Using local serviceAccount.json")
        cred = credentials.Certificate("serviceAccount.json")

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://stock-news-sync-default-rtdb.firebaseio.com/'
    })

# ==========================================
# 2. 종목 및 이름 매핑
# ==========================================
NAME_MAP = {
    # [미국]
    "NVDA": "NVIDIA", "TSLA": "Tesla", "AAPL": "Apple", "AMD": "AMD", 
    "AMZN": "Amazon", "MSFT": "Microsoft", "META": "Meta", "GOOGL": "Alphabet",
    "PLTR": "Palantir", "SOFI": "SoFi", "MARA": "Marathon Digital", "COIN": "Coinbase",
    "INTC": "Intel", "UBER": "Uber", "F": "Ford", "BAC": "Bank of America",
    "QQQ": "Invesco QQQ", "SPY": "SPDR S&P 500", "TQQQ": "ProShares UltraPro",
    "SOXL": "Direxion Semi Bull", "SQQQ": "ProShares UltraPro Short",
    
    # [한국]
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "042700.KS": "한미반도체", "012450.KS": "한화에어로스페이스", "086520.KS": "에코프로",
    "247540.KS": "에코프로비엠", "028300.KS": "HLB", "001440.KS": "대한전선",
    "010130.KS": "고려아연", "034020.KS": "두산에너빌리티"
}

US_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" not in k]
KR_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" in k]

# ==========================================
# 3. 뉴스 수집 함수
# ==========================================

def get_google_news(query):
    try:
        encoded_query = urllib.parse.quote(f"{query} stock")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        if feed.entries:
            return feed.entries[0].title, feed.entries[0].link
    except Exception as e:
        print(f"⚠️ Google News Error ({query}): {e}")
    return "No recent news found", ""

def get_naver_news(query):
    try:
        url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return "뉴스 로딩 실패", ""
        
        data = res.json()
        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            return title, item['link']
    except Exception as e:
        print(f"⚠️ Naver News Error ({query}): {e}")
    return "관련 뉴스 없음", ""

# ==========================================
# 4. 메인 엔진 (1회 실행 로직)
# ==========================================

def calc_change(price, prev_close):
    if prev_close is None or prev_close == 0: return 0.0
    return round(((price - prev_close) / prev_close) * 100, 2)

def get_top_volume_stocks(ticker_list, top_n=10):
    try:
        tickers = yf.Tickers(" ".join(ticker_list))
        ranking = []
        for symbol in ticker_list:
            try:
                t = tickers.tickers[symbol]
                price = t.fast_info['last_price']
                volume = t.fast_info['last_volume']
                prev_close = t.fast_info['previous_close']
                
                if volume is not None and price is not None:
                    ranking.append({
                        "symbol": symbol, 
                        "price": price, 
                        "volume": volume, 
                        "change_percent": calc_change(price, prev_close)
                    })
            except: continue
        return sorted(ranking, key=lambda x: x['volume'], reverse=True)[:top_n]
    except: return []

def run_sync_engine_once():
    """GitHub Actions용 1회 실행 함수"""
    print("🚀 Starting Data Sync...")
    
    try:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # [A] 지수/지표 업데이트
        config = {
            "domestic_indices": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
            "global_indices": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
            "indicators": { "USD_KRW": "USDKRW=X", "US_10Y": "^TNX", "BTC": "BTC-USD", "Gold": "GC=F" }
        }

        for category, items in config.items():
            updates = {}
            path = f"market_indices/{'domestic' if category == 'domestic_indices' else 'global'}" if "indices" in category else "key_indicators"
            for name, ticker in items.items():
                try:
                    t = yf.Ticker(ticker)
                    price = t.fast_info['last_price']
                    prev = t.fast_info['previous_close']
                    updates[name] = {"price": round(price, 2), "change_percent": calc_change(price, prev), "updated_at": now_str}
                except: continue
            db.reference(path).update(updates)

        # [B] 종목 및 뉴스 업데이트
        us_stocks = get_top_volume_stocks(US_CANDIDATES, 10)
        kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 10)
        
        final_feed = {}
        combined_list = us_stocks + kr_stocks
        
        print(f"📊 Analyzing {len(combined_list)} stocks...")

        for item in combined_list:
            symbol = item['symbol']
            company_name = NAME_MAP.get(symbol, symbol)
            country = "US" if symbol in US_CANDIDATES else "KR"
            
            # 뉴스 소스 분기
            if country == "US":
                news_title, news_link = get_google_news(company_name)
            else:
                news_title, news_link = get_naver_news(company_name)
            
            safe_key = symbol.replace(".", "_")
            final_feed[safe_key] = {
                "company_name": company_name,
                "price": round(item['price'], 2),
                "volume": int(item['volume']),
                "change_percent": item['change_percent'],
                "news_title": news_title,
                "news_url": news_link,
                "country": country,
                "updated_at": now_str
            }
            print(f"   👉 [{country}] {company_name}: {news_title[:30]}...")
            time.sleep(0.1) 

        db.reference('sync_feed').set(final_feed)
        print(f"✅ Sync Complete Successfully at {now_str}")

    except Exception as e:
        print(f"❌ Critical Error during sync: {e}")
        # GitHub Actions가 에러를 인지하도록 예외를 다시 던짐
        raise e 

if __name__ == "__main__":
    run_sync_engine_once()