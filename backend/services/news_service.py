import os
import re
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from rank_bm25 import BM25Okapi
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tavily import TavilyClient
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)  # [P6 Fix] logging 모듈 통일

# 모듈 레벨 초기화 — Lambda warm start 시 재사용
tavily_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
_vader = SentimentIntensityAnalyzer()


def _bm25_rerank(query: str, results: list[dict], top_n: int = 3) -> list[dict]:
    """BM25로 뉴스 관련성 재랭킹, top_n개 반환."""
    if len(results) <= top_n:
        return results
    corpus = [(r['title'] + ' ' + r['content']).lower().split() for r in results]
    scores = BM25Okapi(corpus).get_scores(query.lower().split())
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [r for r, _ in ranked[:top_n]]


def _add_sentiment(links: list[dict]) -> list[dict]:
    """VADER로 제목 기반 감성 점수(-1.0~+1.0)를 메타데이터로 추가."""
    for link in links:
        scores = _vader.polarity_scores(link.get('title', ''))
        link['sentiment'] = round(scores['compound'], 3)
    return links


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

    파이프라인:
    Tavily(max=5, days=1) → score≥0.5 필터 → BM25 재랭킹(top-3)
    → context/links 생성 → VADER 감성 추가 → dedup → 반환
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

        # BM25 재랭킹 — 쿼리 키워드 기준 관련성 높은 top-3 선택
        results = _bm25_rerank(query, results)

        # 1. AI에게 먹여줄 '본문 덩어리' (Context) 만들기
        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        # 2. 프론트엔드에 보여줄 '링크 리스트' 만들기
        links = [
            {"title": r['title'], "url": r['url'], "date": r.get('published_date', '')}
            for r in results
        ]

        # VADER 감성 점수 메타데이터 추가 (하드 필터로 사용하지 않음)
        links = _add_sentiment(links)

        # 중복 제거 (URL + 제목 유사도 기준)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("Tavily 검색 실패 (%s): %s", query, e)  # [P6 Fix] print → logger.warning
        return "", []


_html_tag_re = re.compile(r'<[^>]+>')


def get_naver_news(query: str, display: int = 5) -> tuple[str, list[dict]]:
    """
    Naver News API를 이용해 한국어 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인:
    Naver Search API(display=5, sort=date) → HTML 태그 제거 → BM25 재랭킹(top-3)
    → context/links 생성 → VADER 감성 추가 → dedup → 반환
    """
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        logger.warning("NAVER_CLIENT_ID/SECRET 미설정 — 네이버 뉴스 스킵")
        return "", []

    logger.info("Naver 뉴스 검색 시작: %s", query)

    try:
        resp = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={"query": query, "display": display, "sort": "date"},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        # 네이버 API 응답에 포함된 HTML 태그 제거 (예: <b>삼성전자</b>)
        results = [
            {
                "title": _html_tag_re.sub("", item.get("title", "")),
                "content": _html_tag_re.sub("", item.get("description", "")),
                "url": item.get("link", ""),
                "published_date": item.get("pubDate", ""),
            }
            for item in items
        ]

        # BM25 재랭킹
        results = _bm25_rerank(query, results)

        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        links = [
            {"title": r["title"], "url": r["url"], "date": r.get("published_date", "")}
            for r in results
        ]

        links = _add_sentiment(links)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("Naver 뉴스 검색 실패 (%s): %s", query, e)
        return "", []


def get_yahoo_rss_news(query: str, symbol=None):
    """
    Yahoo Finance RSS 피드에서 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인:
    Yahoo RSS(symbol or ^GSPC) → XML 파싱 → BM25 재랭킹(top-3)
    → context/links 생성 → VADER 감성 추가 → dedup → 반환

    실패 시 logger.warning 후 ("", []) 반환.
    """
    ticker = symbol if symbol else "^GSPC"
    url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline"
        f"?s={ticker}&region=US&lang=en-US"
    )

    logger.info("Yahoo RSS 검색 시작: %s (symbol=%s)", query, ticker)

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            logger.warning("Yahoo RSS: channel 요소 없음 (symbol=%s)", ticker)
            return "", []

        results = []
        for item in channel.findall("item"):
            title = item.findtext("title") or ""
            # RSS 2.0의 <link> 태그는 ET.findtext로 읽히지 않아 .tail로 읽어야 함
            link_el = item.find("link")
            item_url = (link_el.tail or "").strip() if link_el is not None else ""
            description = item.findtext("description") or ""
            pub_date = item.findtext("pubDate") or ""

            results.append({
                "title": title,
                "content": description,
                "url": item_url,
                "published_date": pub_date,
            })

        if not results:
            logger.warning("Yahoo RSS: 결과 없음 (symbol=%s)", ticker)
            return "", []

        results = _bm25_rerank(query, results)

        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        links = [
            {"title": r["title"], "url": r["url"], "date": r.get("published_date", "")}
            for r in results
        ]

        links = _add_sentiment(links)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("Yahoo RSS 검색 실패 (%s, symbol=%s): %s", query, ticker, e)
        return "", []


def get_google_rss_news(query: str):
    """
    Google News RSS에서 한국어 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인:
    Google RSS(hl=ko&gl=KR) → XML 파싱 → HTML 태그 제거 → BM25 재랭킹(top-3)
    → context/links 생성 → VADER 감성 추가 → dedup → 반환

    실패 시 ("", []) 반환.
    """
    url = (
        f"https://news.google.com/rss/search"
        f"?q={quote_plus(query)}&hl=ko&gl=KR&ceid=KR:ko"
    )

    logger.info("Google RSS 검색 시작: %s", query)

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            logger.warning("Google RSS: channel 요소 없음 (query=%s)", query)
            return "", []

        results = []
        for item in channel.findall("item"):
            title = _html_tag_re.sub("", item.findtext("title") or "")
            # Google RSS <link>는 리다이렉트 URL이지만 그대로 저장
            link_el = item.find("link")
            item_url = (link_el.tail or "").strip() if link_el is not None else ""
            description = _html_tag_re.sub("", item.findtext("description") or "")
            pub_date = item.findtext("pubDate") or ""

            results.append({
                "title": title,
                "content": description,
                "url": item_url,
                "published_date": pub_date,
            })

        if not results:
            logger.warning("Google RSS: 결과 없음 (query=%s)", query)
            return "", []

        results = _bm25_rerank(query, results)

        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        links = [
            {"title": r["title"], "url": r["url"], "date": r.get("published_date", "")}
            for r in results
        ]

        links = _add_sentiment(links)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("Google RSS 검색 실패 (%s): %s", query, e)
        return "", []


def get_gdelt_news(query: str):
    """
    GDELT v2 Doc API에서 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인:
    GDELT artlist(maxrecords=10) → BM25 재랭킹(top-3)
    → context/links 생성 → VADER 감성 추가 → dedup → 반환

    실패 시 ("", []) 반환.
    """
    url = (
        f'https://api.gdeltproject.org/api/v2/doc/doc'
        f'?query="{quote_plus(query)}"&maxrecords=10&format=json&mode=artlist'
    )

    logger.info("GDELT 검색 시작: %s", query)

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles") or []
        if not articles:
            logger.warning("GDELT: 결과 없음 (query=%s)", query)
            return "", []

        results = []
        for article in articles:
            # seendate 형식: "20230101T000000Z" → "2023-01-01"
            raw_date = article.get("seendate", "")
            try:
                date_str = (
                    f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                    if len(raw_date) >= 8
                    else raw_date
                )
            except Exception:
                date_str = raw_date

            results.append({
                "title": article.get("title", ""),
                "content": article.get("title", ""),  # GDELT artlist는 본문 미제공
                "url": article.get("url", ""),
                "published_date": date_str,
            })

        results = _bm25_rerank(query, results)

        context = "\n\n".join([
            f"[{i+1}. {r['title']}]\n{r['content']}"
            for i, r in enumerate(results)
        ])

        links = [
            {"title": r["title"], "url": r["url"], "date": r.get("published_date", "")}
            for r in results
        ]

        links = _add_sentiment(links)
        links = _deduplicate_links(links)

        return context, links

    except Exception as e:
        logger.warning("GDELT 검색 실패 (%s): %s", query, e)
        return "", []


def get_foreign_news(query: str, symbol=None):
    """
    해외 뉴스 Fallback 체인: Tavily → Yahoo RSS → GDELT

    각 소스에서 links가 비어 있으면 다음 소스로 넘어갑니다.
    """
    context, links = get_tavily_news(query)
    if links:
        return context, links
    context, links = get_yahoo_rss_news(query, symbol)
    if links:
        return context, links
    return get_gdelt_news(query)


def get_korean_news(query: str):
    """
    한국어 뉴스 Fallback 체인: Naver → Google RSS → GDELT

    각 소스에서 links가 비어 있으면 다음 소스로 넘어갑니다.
    """
    context, links = get_naver_news(query)
    if links:
        return context, links
    context, links = get_google_rss_news(query)
    if links:
        return context, links
    return get_gdelt_news(query)
