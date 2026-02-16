from services.news_service import get_tavily_news
from services.ai_service import generate_ai_summary

def test():
    target = "삼성전자"
    print(f"🚀 {target} 테스트 시작...")

    # 1. 뉴스 수집 테스트
    context, links = get_tavily_news(target)
    if context:
        print(f"✅ 뉴스 수집 성공! (링크 {len(links)}개 확보)")
        
        # 2. AI 요약 테스트
        print("🧠 AI 분석 중...")
        summary = generate_ai_summary(target, context)
        print("\n=== AI 요약 결과 ===")
        print(summary)
    else:
        print("❌ 뉴스 수집 실패. API 키나 네트워크를 확인하세요.")

if __name__ == "__main__":
    test()