import os
import logging
from tavily import TavilyClient
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)  # [P6 Fix] logging 모듈 통일

# Tavily 클라이언트 초기화
tavily_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

def get_tavily_news(query: str) -> tuple[str, list[dict]]:  # [P7 Fix] 타입 힌트 추가
    """
    Tavily를 이용해 뉴스 본문(Context)과 링크를 가져옵니다.
    """
    if not tavily:
        logger.error("TAVILY_API_KEY가 없습니다.")  # [P6 Fix] print → logger.error
        return "", []

    logger.info("Tavily 검색 시작: %s", query)  # [P6 Fix] print → logger.info

    try:
        # topic="news" 옵션으로 뉴스 데이터만 필터링
        response = tavily.search(
            query=f"{query} 주가 전망 및 최신 뉴스",
            topic="news",
            max_results=3,  # 무료 쿼리 절약을 위해 3개만 (학생용은 5개까지 늘려도 됨)
            include_answer=False,
            include_raw_content=False
        )

        results = response.get('results', [])

        # 1. AI에게 먹여줄 '본문 덩어리' (Context) 만들기
        # 제목과 내용을 합쳐서 하나의 긴 텍스트로 만듭니다.
        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        # 2. 프론트엔드에 보여줄 '링크 리스트' 만들기
        links = [
            {"title": r['title'], "url": r['url'], "date": r.get('published_date', '')}
            for r in results
        ]

        return context, links

    except Exception as e:
        logger.warning("Tavily 검색 실패 (%s): %s", query, e)  # [P6 Fix] print → logger.warning
        return "", []
