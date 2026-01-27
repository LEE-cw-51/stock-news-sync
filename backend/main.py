import firebase_admin
from firebase_admin import credentials, db
import yfinance as yf
import time
import feedparser
import requests
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 설정 및 API 키 입력
# ==========================================
cred = credentials.Certificate("serviceAccount.json")

# ⚠️ 본인의 Firebase 주소인지 확인하세요!
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://stock-news-sync-default-rtdb.firebaseio.com/' 
})

# ⚠️ [중요] 네이버 개발자 센터에서 발급받은 키를 여기에 넣으세요
NAVER_CLIENT_ID = "zhHWNVx4FqeKbc2IbQoM"
NAVER_CLIENT_SECRET = "S6ay2XGyv3"

# ==========================================
# 2. 종목 및 이름 매핑 (검색 정확도 향상용)
# ==========================================
NAME_MAP = {
    # [미국] 티커: 검색용_영문명
    "NVDA": "NVIDIA", "TSLA": "Tesla", "AAPL": "Apple", "AMD": "AMD", 
    "AMZN": "Amazon", "MSFT": "Microsoft", "META": "Meta", "GOOGL": "Alphabet",
    "PLTR": "Palantir", "SOFI": "SoFi", "MARA": "Marathon Digital", "COIN": "Coinbase",
    "INTC": "Intel", "UBER": "Uber", "F": "Ford", "BAC": "Bank of America",
    "QQQ": "Invesco QQQ", "SPY": "SPDR S&P 500", "TQQQ": "ProShares UltraPro",
    "SOXL": "Direxion Semi Bull", "SQQQ": "ProShares UltraPro Short",
    
    # [한국] 티커: 검색용_한글명
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "042700.KS": "한미반도체", "012450.KS": "한화에어로스페이스", "086520.KS": "에코프로",
    "247540.KS": "에코프로비엠", "028300.KS": "HLB", "001440.KS": "대한전선",
    "010130.KS": "고려아연", "034020.KS": "두산에너빌리티"
}

# 자동 분류
US_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" not in k]
KR_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" in k]

# ==========================================
# 3. 뉴스 수집 함수 (구글 RSS + 네이버 API)
# ==========================================

# [Google News RSS] - 미국 주식용 (무료, 무제한)
def get_google_news(query):
    try:
        # 검색어 뒤에 'stock'을 붙여서 주식 관련 뉴스만 필터링
        encoded_query = urllib.parse.quote(f"{query} stock")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(url)
        if feed.entries:
            title = feed.entries[0].title
            link = feed.entries[0].link
            return title, link
    except Exception as e:
        print(f"⚠️ 구글 뉴스 에러 ({query}): {e}")
    return "No recent news found", ""

# [Naver Search API] - 한국 주식용 (빠름, 정확함)
def get_naver_news(query):
    try:
        url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        res = requests.get(url, headers=headers)
        
        # 에러 코드 확인 (401이면 키 문제)
        if res.status_code != 200:
            print(f"⚠️ 네이버 API 에러 코드: {res.status_code}")
            return "뉴스 로딩 실패 (API 키 확인)", ""

        data = res.json()
        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            # 네이버가 주는 HTML 태그(<b> 등) 청소
            title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item['link']
            return title, link
    except Exception as e:
        print(f"⚠️ 네이버 뉴스 에러 ({query}): {e}")
    return "관련 뉴스 없음", ""

# ==========================================
# 4. 메인 엔진 로직
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

def run_sync_engine():
    ref_indices = db.reference('market_indices')
    ref_indicators = db.reference('key_indicators')
    ref_feed = db.reference('sync_feed') 

    # 지표 설정
    config = {
        "domestic_indices": { "KOSPI": "^KS11", "KOSDAQ": "^KQ11" },
        "global_indices": { "S&P500": "^GSPC", "NASDAQ": "^IXIC" },
        "indicators": { "USD_KRW": "USDKRW=X", "US_10Y": "^TNX", "BTC": "BTC-USD", "Gold": "GC=F" }
    }

    print("🚀 Auto-Volume Sync (Google + Naver News Engine) Started...")

    while True:
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # [A] 지수 업데이트
            for category in ["domestic_indices", "global_indices", "indicators"]:
                updates = {}
                path = f"market_indices/{'domestic' if category == 'domestic_indices' else 'global'}" if "indices" in category else "key_indicators"
                
                for name, ticker in config[category].items():
                    try:
                        t = yf.Ticker(ticker)
                        price = t.fast_info['last_price']
                        prev = t.fast_info['previous_close']
                        updates[name] = {"price": round(price, 2), "change_percent": calc_change(price, prev), "updated_at": now_str}
                    except: continue
                db.reference(path).update(updates)

            # [B] 종목 선정 및 뉴스 매칭
            print("📊 거래량 분석 및 뉴스 수집 중...")
            us_stocks = get_top_volume_stocks(US_CANDIDATES, 10)
            kr_stocks = get_top_volume_stocks(KR_CANDIDATES, 10)
            
            final_feed = {}
            combined_list = us_stocks + kr_stocks
            
            for item in combined_list:
                symbol = item['symbol']
                # 이름 매핑 (없으면 티커 사용)
                company_name = NAME_MAP.get(symbol, symbol)
                country = "US" if symbol in US_CANDIDATES else "KR"
                
                # ⭐️ [핵심] 국가별 뉴스 소스 분기 처리
                if country == "US":
                    news_title, news_link = get_google_news(company_name)
                else:
                    news_title, news_link = get_naver_news(company_name)
                
                # 데이터 패키징
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
                
                # 로그 출력 (확인용)
                print(f"   👉 [{country}] {company_name}: {news_title[:30]}...")
                time.sleep(0.1) # API 예의상 딜레이

            # Firebase 전송
            ref_feed.set(final_feed)
            print(f"✅ Sync Complete ({now_str})")
            print("------------------------------------------------")
            time.sleep(60)

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_sync_engine()