# ==========================================
# 1. 거시경제 (Macro) 키워드
# ==========================================
MACRO_KEYWORDS = [
    "미국 금리", "FOMC", "미국 소비자물가지수", "국제 유가", 
    "환율 전망", "미국 고용 지표", "AI 산업 전망", "반도체 업황"
]

# ==========================================
# 2. 내 포트폴리오 (보유 종목)
# ==========================================
MY_PORTFOLIO = {
    "NVDA": {"name": "NVIDIA", "sector": "AI/반도체", "shares": 50},
    "005930.KS": {"name": "삼성전자", "sector": "반도체/메모리", "shares": 100},
    "TSLA": {"name": "Tesla", "sector": "전기차", "shares": 30}
}

# ==========================================
# 3. 관심 종목 (Watchlist) - 단순히 지켜보는 종목
# ==========================================
WATCHLIST = {
    "AAPL": {"name": "Apple", "sector": "IT/디바이스"},
    "MSFT": {"name": "Microsoft", "sector": "클라우드"},
    "035420.KS": {"name": "NAVER", "sector": "플랫폼"}
}

# (기존 호환성을 위해 합친 리스트도 유지)
ALL_TICKERS = list(MY_PORTFOLIO.keys()) + list(WATCHLIST.keys())
US_CANDIDATES = [k for k in ALL_TICKERS if ".KS" not in k]
KR_CANDIDATES = [k for k in ALL_TICKERS if ".KS" in k]
NAME_MAP = {**MY_PORTFOLIO, **WATCHLIST} # 전체 매핑 정보