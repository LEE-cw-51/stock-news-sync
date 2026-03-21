import os
import logging
from difflib import SequenceMatcher
from tavily import TavilyClient
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)  # [P6 Fix] logging 모듈 통일

# Tavily 클라이언트 초기화
tavily_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_key) if tavily_key else None


def _deduplicate_links(links: list[dict]) -> list[dict]:
    """URL 해시 및 제목 유사도 기준으로 중복 뉴스를 제거합니다."""
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    result: list[dict] = []

    for link in links:
        url = link.get("url", "")
        title = link.get("title", "")

        # URL 중복 제거
        if url in seen_urls:
            continue

        # 제목 유사도 중복 제거 (0.85 이상이면 동일 기사로 판단)
        is_duplicate = any(
            SequenceMatcher(None, title, t).ratio() >= 0.85
            for t in seen_titles
        )
        if is_duplicate:
            continue

        seen_urls.add(url)
        seen_titles.append(title)
        result.append(link)

    return result


def get_tavily_news(query: str) -> tuple[str, list[dict]]:  # [P7 Fix] 타입 힌트 추가
    """
    Tavily를 이용해 뉴스 본문(Context)과 링크를 가져옵니다.
    """
    if not tavily:
        logger.error("TAVILY_API_KEY가 없습니다.")  # [P6 Fix] print → logger.error
        return "", []

    logger.info("Tavily 검색 시작: %s", query)  # [P6 Fix] print → logger.info

    try:
        # topic="news" + days=1로 최신 24시간 뉴스만 수집
        try:
            response = tavily.search(
                query=f"{query} 주가 전망 및 최신 뉴스",
                topic="news",
                max_results=5,  # score 필터 후 최종 3개 선택을 위해 여유있게 수집
                days=1,
                include_answer=False,
                include_raw_content=False
            )
        except TypeError:
            # days 파라미터 미지원 SDK 버전 폴백
            response = tavily.search(
                query=f"{query} 주가 전망 및 최신 뉴스",
                topic="news",
                max_results=5,
                include_answer=False,
                include_raw_content=False
            )

        results = response.get('results', [])

        # score 기준 관련성 필터링 (0.5 미만 제거)
        results = [r for r in results if r.get('score', 0) >= 0.5]

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

        # 중복 제거 (URL + 제목 유사도 기준)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("Tavily 검색 실패 (%s): %s", query, e)  # [P6 Fix] print → logger.warning
        return "", []
