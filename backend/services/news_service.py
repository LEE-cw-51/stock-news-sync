"""
news_service.py — 뉴스 소스별 fetch + light prefilter/reranking 함수 모음

각 함수는 뉴스 소스별 raw 데이터를 가져온 뒤,
  - score 기반 프리필터링(Tavily: ≥0.5)과
  - BM25 기준 가벼운 재랭킹(top-3)
까지를 수행하여 (context_str, links_list, results_list) 형태로 반환한다.
최종 Contextual Compression·VADER 필터·중복 제거 등 전체 파이프라인 오케스트레이션은
retrieval_pipeline.py에서 담당한다.

Fallback 체인:
  해외(US): get_foreign_news() → Tavily → Yahoo RSS → GDELT
  국내(KR): get_korean_news()  → Naver  → Google RSS → GDELT
"""

import os
import re
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote_plus, quote
import requests
from rank_bm25 import BM25Okapi
from tavily import TavilyClient
from dotenv import load_dotenv

# .env 파일 로드 — __file__ 기준 절대경로 (워크트리 CWD 무관)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

# 모듈 레벨 초기화 — Lambda warm start 시 재사용
tavily_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

_html_tag_re = re.compile(r'<[^>]+>')


def _bm25_rerank(query: str, results: list[dict], top_n: int = 3) -> list[dict]:
    """BM25로 뉴스 관련성 재랭킹, top_n개 반환."""
    if len(results) <= top_n:
        return results
    corpus = [(r['title'] + ' ' + r['content']).lower().split() for r in results]
    scores = BM25Okapi(corpus).get_scores(query.lower().split())
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [r for r, _ in ranked[:top_n]]


def _build_raw_output(results: list[dict]) -> tuple[str, list[dict], list[dict]]:
    """results 리스트로부터 (context 문자열, links 리스트, results 리스트)를 생성한다."""
    context = "\n\n".join([
        f"[{i+1}. {r['title']}]\n{r['content']}"
        for i, r in enumerate(results)
    ])
    links = [
        {"title": r['title'], "url": r['url'], "date": r.get('published_date', '')}
        for r in results
    ]
    return context, links, results


def get_tavily_news(query: str) -> tuple[str, list[dict], list[dict]]:
    """
    Tavily를 이용해 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인: Tavily(max=5, days=1) → score≥0.5 필터 → BM25 재랭킹(top-3)
    추가 필터링은 retrieval_pipeline.py QualityPipeline 담당.
    """
    if not tavily:
        logger.error("TAVILY_API_KEY가 없습니다.")
        return "", [], []

    logger.info("Tavily 검색 시작: %s", query)

    try:
        try:
            response = tavily.search(
                query=f"{query} 주가 전망 및 최신 뉴스",
                topic="news",
                max_results=5,
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

        # score 기준 관련성 필터링
        results = [r for r in results if r.get('score', 0) >= 0.5]

        # BM25 재랭킹
        results = _bm25_rerank(query, results)

        return _build_raw_output(results)

    except Exception as e:
        logger.warning("Tavily 검색 실패 (%s): %s", query, e)
        return "", [], []


def get_naver_news(query: str, display: int = 5) -> tuple[str, list[dict], list[dict]]:
    """
    Naver News API를 이용해 한국어 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인: Naver Search API(display=5, sort=date) → HTML 태그 제거 → BM25 재랭킹(top-3)
    추가 필터링은 retrieval_pipeline.py QualityPipeline 담당.
    """
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        logger.warning("NAVER_CLIENT_ID/SECRET 미설정 — 네이버 뉴스 스킵")
        return "", [], []

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

        results = [
            {
                "title": _html_tag_re.sub("", item.get("title", "")),
                "content": _html_tag_re.sub("", item.get("description", "")),
                "url": item.get("link", ""),
                "published_date": item.get("pubDate", ""),
            }
            for item in items
        ]

        results = _bm25_rerank(query, results)
        return _build_raw_output(results)

    except Exception as e:
        logger.warning("Naver 뉴스 검색 실패 (%s): %s", query, e)
        return "", [], []


def get_yahoo_rss_news(query: str, symbol=None) -> tuple[str, list[dict], list[dict]]:
    """
    Yahoo Finance RSS 피드에서 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인: Yahoo RSS(symbol or ^GSPC) → XML 파싱 → BM25 재랭킹(top-3)
    추가 필터링은 retrieval_pipeline.py QualityPipeline 담당.
    """
    ticker = symbol if symbol else "^GSPC"
    url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline"
        f"?s={ticker}&region=US&lang=en-US"
    )

    logger.info("Yahoo RSS 검색 시작: %s (symbol=%s)", query, ticker)

    try:
        resp = requests.get(
            url, timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            logger.warning("Yahoo RSS: channel 요소 없음 (symbol=%s)", ticker)
            return "", [], []

        results = []
        for item in channel.findall("item"):
            title = item.findtext("title") or ""
            link_el = item.find("link")
            item_url = (link_el.text or "").strip() if link_el is not None else ""
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
            return "", [], []

        results = _bm25_rerank(query, results)
        return _build_raw_output(results)

    except Exception as e:
        logger.warning("Yahoo RSS 검색 실패 (%s, symbol=%s): %s", query, ticker, e)
        return "", [], []


def get_google_rss_news(query: str) -> tuple[str, list[dict], list[dict]]:
    """
    Google News RSS에서 한국어 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인: Google RSS(hl=ko&gl=KR) → XML 파싱 → HTML 태그 제거 → BM25 재랭킹(top-3)
    추가 필터링은 retrieval_pipeline.py QualityPipeline 담당.
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
            return "", [], []

        results = []
        for item in channel.findall("item"):
            title = _html_tag_re.sub("", item.findtext("title") or "")
            link_el = item.find("link")
            item_url = (link_el.text or "").strip() if link_el is not None else ""
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
            return "", [], []

        results = _bm25_rerank(query, results)
        return _build_raw_output(results)

    except Exception as e:
        logger.warning("Google RSS 검색 실패 (%s): %s", query, e)
        return "", [], []


def get_gdelt_news(query: str) -> tuple[str, list[dict], list[dict]]:
    """
    GDELT v2 Doc API에서 뉴스 본문(Context)과 링크를 가져옵니다.

    파이프라인: GDELT artlist(maxrecords=10) → BM25 재랭킹(top-3)
    추가 필터링은 retrieval_pipeline.py QualityPipeline 담당.
    """
    url = (
        f'https://api.gdeltproject.org/api/v2/doc/doc'
        f'?query={quote(query)}&maxrecords=10&format=json&mode=artlist'
    )

    logger.info("GDELT 검색 시작: %s", query)

    try:
        import time as _time
        _time.sleep(6)  # GDELT: 5초에 1회 제한 정책 준수
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles") or []
        if not articles:
            logger.warning("GDELT: 결과 없음 (query=%s)", query)
            return "", [], []

        results = []
        for article in articles:
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
        return _build_raw_output(results)

    except Exception as e:
        logger.warning("GDELT 검색 실패 (%s): %s", query, e)
        return "", [], []


def get_foreign_news(query: str, symbol=None) -> tuple[str, list[dict], list[dict]]:
    """
    해외 뉴스 Fallback 체인: Tavily → Yahoo RSS → GDELT

    각 소스에서 links가 비어 있으면 다음 소스로 넘어갑니다.
    """
    context, links, results = get_tavily_news(query)
    if links:
        return context, links, results
    context, links, results = get_yahoo_rss_news(query, symbol)
    if links:
        return context, links, results
    return get_gdelt_news(query)


def get_korean_news(query: str) -> tuple[str, list[dict], list[dict]]:
    """
    한국어 뉴스 Fallback 체인: Naver → Google RSS → GDELT

    각 소스에서 links가 비어 있으면 다음 소스로 넘어갑니다.
    """
    context, links, results = get_naver_news(query)
    if links:
        return context, links, results
    context, links, results = get_google_rss_news(query)
    if links:
        return context, links, results
    return get_gdelt_news(query)
