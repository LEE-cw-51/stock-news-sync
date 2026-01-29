# 내용을 기반으로 확장
NAME_MAP = {
    # [미국]
    "NVDA": {"name": "NVIDIA", "sector": "AI/반도체"},
    "TSLA": {"name": "Tesla", "sector": "전기차"},
    "AAPL": {"name": "Apple", "sector": "IT/디바이스"},
    "AMD": {"name": "AMD", "sector": "AI/반도체"},
    "AMZN": {"name": "Amazon", "sector": "이커머스/클라우드"},
    "MSFT": {"name": "Microsoft", "sector": "소프트웨어/클라우드"},
    "META": {"name": "Meta", "sector": "SNS/AI"},
    "GOOGL": {"name": "Alphabet", "sector": "검색/AI"},
    "PLTR": {"name": "Palantir", "sector": "빅데이터/AI"},
    
    # [한국]
    "005930.KS": {"name": "삼성전자", "sector": "반도체/IT"},
    "000660.KS": {"name": "SK하이닉스", "sector": "반도체/메모리"},
    "005380.KS": {"name": "현대차", "sector": "자동차"},
    "035420.KS": {"name": "NAVER", "sector": "플랫폼/AI"},
    "035720.KS": {"name": "카카오", "sector": "플랫폼/모바일"}
}

US_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" not in k]
KR_CANDIDATES = [k for k, v in NAME_MAP.items() if ".KS" in k]

# 동종 투자자 비교를 위한 벤치마크 데이터 (예시)
PEER_BENCHMARKS = {
    "20s": {"avg_return": 2.1, "tech_weight": 48},
    "30s": {"avg_return": 1.8, "tech_weight": 35}
}