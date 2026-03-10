import sys
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from services.news_service import get_tavily_news
from services.ai_service import generate_ai_summary
from services.market_service import get_market_indices

def test_market():
    print("[TEST] 시장 지수 수집 테스트...")
    result = get_market_indices({"KOSPI": "^KS11", "KOSDAQ": "^KQ11"})
    if result:
        for name, data in result.items():
            print(f"  {name}: {data['price']} ({data['change_percent']:+.2f}%)")
        print(f"[OK] 시장 지수 수집 성공 ({len(result)}개)")
    else:
        print("[FAIL] 시장 지수 수집 실패 — yfinance 연결 또는 티커 확인 필요")

def test_news_and_ai():
    target = "삼성전자"
    print(f"[TEST] {target} 뉴스 + AI 테스트...")

    context, links = get_tavily_news(target)
    if context:
        print(f"[OK] 뉴스 수집 성공! (링크 {len(links)}개)")
        summary = generate_ai_summary(target, context)
        print("=== AI 요약 결과 ===")
        print(summary)
    else:
        print("[FAIL] 뉴스 수집 실패. API 키나 네트워크를 확인하세요.")

if __name__ == "__main__":
    test_market()
    print()
    test_news_and_ai()
