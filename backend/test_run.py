import sys
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from services.news_service import get_tavily_news
from services.ai_service import generate_ai_summary
from services.market_service import get_market_indices


def test_rss_fallback():
    """Yahoo RSS, Google RSS, GDELT 단독 동작 확인"""
    from services.news_service import get_yahoo_rss_news, get_google_rss_news, get_gdelt_news

    print("\n[TEST] Yahoo Finance RSS 테스트...")
    context, links = get_yahoo_rss_news("NVIDIA", symbol="NVDA")
    if links:
        print(f"  [OK] Yahoo RSS: {len(links)}개 링크")
    else:
        print("  [WARN] Yahoo RSS: 링크 없음 (네트워크 또는 RSS 변경 가능성)")

    print("[TEST] Google News RSS 테스트 (한국어)...")
    context, links = get_google_rss_news("삼성전자 주가")
    if links:
        print(f"  [OK] Google RSS: {len(links)}개 링크")
    else:
        print("  [WARN] Google RSS: 링크 없음")

    print("[TEST] GDELT API v2 테스트...")
    context, links = get_gdelt_news("NVIDIA stock market")
    if links:
        print(f"  [OK] GDELT: {len(links)}개 링크")
    else:
        print("  [WARN] GDELT: 링크 없음")

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

        # glossary_terms / flow_explanation 필드 검증
        result = summary
        glossary = result.get("glossary_terms") if isinstance(result, dict) else None
        flow = result.get("flow_explanation") if isinstance(result, dict) else None

        if isinstance(glossary, list):
            print(f"  glossary_terms: {len(glossary)}개 — {glossary}")
        else:
            print(f"  glossary_terms 없음 (LLM 누락 또는 구형 응답)")

        if isinstance(flow, str) and flow:
            print(f"  flow_explanation: {flow[:80]}...")
        else:
            print(f"  flow_explanation 없음 (LLM 누락 또는 구형 응답)")
    else:
        print("[FAIL] 뉴스 수집 실패. API 키나 네트워크를 확인하세요.")

if __name__ == "__main__":
    test_market()
    print()
    test_news_and_ai()
    print()
    test_rss_fallback()
