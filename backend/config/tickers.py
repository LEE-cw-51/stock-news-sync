"""
[Configuration Manager]
사용자의 데이터(포트폴리오, 관심종목)를 정의하고, 
이를 기반으로 AI 검색 키워드를 동적으로 생성하는 설정 파일입니다.
"""

# ==========================================
# [PART 1] 사용자 데이터 (Mock Database)
# ==========================================
# 추후 로그인 기능이 구현되면, 이 부분은 DB(Firebase)에서 
# user_data = db.get(user_id) 형태로 대체됩니다.
# ==========================================

USER_PROFILE = {
    "username": "Investor_01",
    "portfolio": {
        "NVDA": {"name": "NVIDIA", "sector": "AI & Semiconductor", "shares": 50},
        "005930.KS": {"name": "Samsung Electronics", "sector": "Memory Chip", "shares": 100},
        "TSLA": {"name": "Tesla", "sector": "EV & Automotive", "shares": 30}
    },
    "watchlist": {
        "AAPL": {"name": "Apple", "sector": "Consumer Electronics"},
        "MSFT": {"name": "Microsoft", "sector": "Cloud & AI"},
        "035420.KS": {"name": "NAVER", "sector": "Platform & Internet"}
    },
    # 사용자가 특별히 관심 있어 하는 거시 경제 주제 (옵션)
    "interests": ["Interest Rates", "Exchange Rates"] 
}


# ==========================================
# [PART 2] 로직 엔진 (Dynamic Logic)
# ==========================================
# 위 데이터를 바탕으로 프로그램이 사용할 변수들을 계산합니다.
# 데이터가 변경되면 결과값도 자동으로 바뀝니다.
# ==========================================

def extract_sectors(profile):
    """사용자 포트폴리오에서 중복 없이 관심 섹터를 추출합니다."""
    sectors = set()
    
    # 포트폴리오와 관심종목 모두에서 섹터 수집
    all_items = {**profile['portfolio'], **profile['watchlist']}
    for info in all_items.values():
        if 'sector' in info:
            sectors.add(info['sector'])
            
    # 토큰 절약을 위해 최대 3개까지만 중요 섹터로 선정
    return list(sectors)[:3]

def generate_keywords(profile, sectors):
    """최적화된 AI 검색 키워드를 생성합니다."""
    
    # 1. 섹터 키워드 (예: "AI & Semiconductor, EV")
    sector_str = ", ".join(sectors)
    
    # 2. 동적 키워드 리스트 구성
    keywords = [
        # [공통] 글로벌 경제 핵심 (사용자 관심사 반영)
        f"Global Market Trends & {', '.join(profile.get('interests', []))}",
        
        # [개인화] 내 보유 종목 관련 산업 전망
        f"Market Outlook for: {sector_str} Industry"
    ]
    return keywords

# ==========================================
# [PART 3] 외부 노출 변수 (Exports)
# ==========================================
# main.py나 news_service.py는 이 변수들만 가져다 씁니다.
# 내부 로직이 아무리 복잡해도, 외부에서는 깔끔한 리스트만 보게 됩니다.
# ==========================================

# 1. 키워드 생성 실행
_active_sectors = extract_sectors(USER_PROFILE)
MACRO_KEYWORDS = generate_keywords(USER_PROFILE, _active_sectors)

# 2. 포트폴리오 및 관심종목 매핑
MY_PORTFOLIO = USER_PROFILE['portfolio']
WATCHLIST = USER_PROFILE['watchlist']

# 3. 전체 종목 리스트 및 매핑 (자동 계산)
ALL_TICKERS = list(MY_PORTFOLIO.keys()) + list(WATCHLIST.keys())
NAME_MAP = {**MY_PORTFOLIO, **WATCHLIST}

# 4. 국가별 티커 분류 (야후 파이낸스 기준)
US_CANDIDATES = [t for t in ALL_TICKERS if ".KS" not in t]
KR_CANDIDATES = [t for t in ALL_TICKERS if ".KS" in t]

# 디버깅용 출력 (로컬 실행 시에만 보임)
if __name__ == "__main__":
    print(f"✅ User: {USER_PROFILE['username']}")
    print(f"✅ Generated Keywords: {MACRO_KEYWORDS}")
    print(f"✅ Tracking Tickers: {len(ALL_TICKERS)} items")