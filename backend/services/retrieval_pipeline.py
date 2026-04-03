"""
retrieval_pipeline.py — Modular RAG 파이프라인 추상화

구조:
  BasePipeline          — 인터페이스 (retrieve 메서드)
  QualityPipeline       — BM25 + Contextual Compression + VADER 필터 (현재 기본값)
  get_pipeline()        — 라우터 함수 (추후 category/market/user_tier 기반 확장)

향후 확장 경로:
  SemanticPipeline      — Gemini Embedding API + BM25 Hybrid
  PersonalizedPipeline  — per-user 관심종목 기반 컨텍스트 구성
"""

import re
import logging
from abc import ABC, abstractmethod
from difflib import SequenceMatcher

from rank_bm25 import BM25Okapi
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

try:
    from backend.services.news_service import get_foreign_news, get_korean_news
except ModuleNotFoundError:
    from services.news_service import get_foreign_news, get_korean_news

logger = logging.getLogger(__name__)

_vader = SentimentIntensityAnalyzer()


# =============================================================================
# 공유 유틸리티
# =============================================================================

def _bm25_rerank(query: str, results: list[dict], top_n: int = 3) -> list[dict]:
    """BM25로 뉴스 관련성 재랭킹, top_n개 반환."""
    if len(results) <= top_n:
        return results
    corpus = [(r["title"] + " " + r["content"]).lower().split() for r in results]
    scores = BM25Okapi(corpus).get_scores(query.lower().split())
    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
    return [r for r, _ in ranked[:top_n]]


def _add_sentiment(links: list[dict]) -> list[dict]:
    """VADER로 제목 기반 감성 점수(-1.0~+1.0)를 메타데이터로 추가."""
    for link in links:
        scores = _vader.polarity_scores(link.get("title", ""))
        link["sentiment"] = round(scores["compound"], 3)
    return links


def _deduplicate(items: list[dict]) -> list[dict]:
    """URL + 제목 유사도 기준으로 중복 기사를 제거합니다.

    url이 비어 있는 경우 URL 기반 중복 체크를 건너뛰고 제목 유사도만 사용합니다.
    """
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    result: list[dict] = []
    for item in items:
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        if url and url in seen_urls:
            continue
        if title and any(
            SequenceMatcher(None, title, t).ratio() >= 0.85
            for t in seen_titles
        ):
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.append(title)
        result.append(item)
    return result


# =============================================================================
# BasePipeline
# =============================================================================

class BasePipeline(ABC):
    """RAG 파이프라인 인터페이스. 모든 파이프라인은 retrieve()를 구현한다."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        symbol: str | None = None,
        market: str = "us",
    ) -> tuple[str, list[dict]]:
        """
        Args:
            query:  종목명 또는 키워드 (예: "NVIDIA", "금리 인상")
            symbol: 티커 심볼 (예: "NVDA", "005930.KS")
            market: "us" | "kr"
        Returns:
            (context_str, links_list)
        """


# =============================================================================
# QualityPipeline
# =============================================================================

class QualityPipeline(BasePipeline):
    """
    BM25 재랭킹 + Contextual Compression + VADER 필터 파이프라인.

    개선 사항 (news_service.py 인라인 로직 대비):
    - 최소 본문 길이 필터: len(content) < 80 stub 기사 제거
    - Contextual Compression: 기사 전문 대신 BM25 상위 2문장만 context에 포함
    - VADER hard filter: |compound| < 0.1 완전 중립 기사 제거
    """

    MIN_CONTENT_LEN = 80
    VADER_THRESHOLD = 0.1
    COMPRESS_TOP_N = 2

    def _compress(self, content: str, query: str) -> str:
        """
        기사 본문을 문장 단위로 분리하고 BM25로 쿼리 관련도 높은
        상위 COMPRESS_TOP_N 문장만 반환한다.
        """
        sentences = [
            s.strip()
            for s in re.split(r"[.!?。\n]", content)
            if len(s.strip()) > 20
        ]
        if len(sentences) <= self.COMPRESS_TOP_N:
            return content
        corpus = [s.lower().split() for s in sentences]
        scores = BM25Okapi(corpus).get_scores(query.lower().split())
        ranked = sorted(zip(sentences, scores), key=lambda x: x[1], reverse=True)
        return ". ".join(s for s, _ in ranked[: self.COMPRESS_TOP_N])

    def _build_context(self, results: list[dict], query: str) -> str:
        """압축된 문장 기반 context 문자열 생성."""
        parts = []
        for i, r in enumerate(results):
            compressed = self._compress(r["content"], query)
            parts.append(f"[{i + 1}. {r['title']}]\n{compressed}")
        return "\n\n".join(parts)

    def retrieve(
        self,
        query: str,
        symbol: str | None = None,
        market: str = "us",
    ) -> tuple[str, list[dict]]:
        # 1. 소스에서 구조화 데이터 fetch (news_service.py 담당)
        if market == "kr":
            raw_context, links, results = get_korean_news(query)
        else:
            raw_context, links, results = get_foreign_news(query, symbol)

        if not links:
            return raw_context, links

        # 2. 최소 본문 길이 필터 (GDELT 등 title-only 결과가 전부 걸러지면 원본 유지)
        original_results = results
        filtered_results = [r for r in results if len(r.get("content", "")) >= self.MIN_CONTENT_LEN]
        if filtered_results:
            results = filtered_results
        else:
            logger.warning(
                "[QualityPipeline] 최소 길이 필터 후 결과 없음 — 원본 유지 (query=%s)",
                query,
            )
            results = original_results

        # 3. BM25 재랭킹
        results = _bm25_rerank(query, results)

        # 4. VADER hard filter — 완전 중립 기사 제거
        scored = []
        for r in results:
            compound = abs(_vader.polarity_scores(r.get("title", ""))["compound"])
            if compound >= self.VADER_THRESHOLD:
                scored.append(r)
        # 필터 후 결과가 없으면 원래 results 유지 (정보량 0 방지)
        if scored:
            results = scored
        else:
            logger.info("[QualityPipeline] VADER 필터 후 결과 없음 — 원본 유지 (query=%s)", query)

        # 5. 중복 제거 — results 단계에서 수행하여 context·links 기사 집합 일치 보장
        results = _deduplicate(results)

        # 6. Contextual Compression으로 context 생성
        context = self._build_context(results, query)

        # 7. links 정리: VADER 점수 메타데이터
        final_links = [
            {
                "title": r["title"],
                "url": r["url"],
                "date": r.get("published_date") or r.get("date", ""),
            }
            for r in results
        ]
        final_links = _add_sentiment(final_links)

        logger.info(
            "[QualityPipeline] retrieve 완료 (query=%s, 기사=%d개)", query, len(final_links)
        )
        return context, final_links


# =============================================================================
# PipelineRouter
# =============================================================================

def get_pipeline(category: str = "watchlist", market: str = "us") -> BasePipeline:
    """
    category / market 조합에 따라 최적 파이프라인을 반환한다.

    현재: 항상 QualityPipeline 반환.
    추후 확장:
        "portfolio" + 프리미엄 유저 → SemanticPipeline
        per-user 개인화 → PersonalizedPipeline
    """
    # TODO: category / user_tier 기반 라우팅 추가
    return QualityPipeline()
