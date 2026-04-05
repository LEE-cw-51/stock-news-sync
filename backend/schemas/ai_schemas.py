# =============================================================================
# AI 요약 응답 스키마 (Pydantic v2)
# Phase 1: 단일 통합 스키마 (AISummarySchema)
# Phase 2: Schema A(Fast) / Schema B(Deep)로 분리 예정
# =============================================================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List


class GlossaryTermModel(BaseModel):
    """금융 용어 정의 (glossary_terms 배열 내 각 항목)"""

    term: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="금융 용어명 (예: PER, EPS, 매도 불균형)"
    )
    definition: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="용어의 한 줄 정의"
    )

    @field_validator('term', 'definition', mode='before')
    @classmethod
    def strip_whitespace(cls, v):
        """앞뒤 공백 제거"""
        return v.strip() if isinstance(v, str) else v


class AISummarySchema(BaseModel):
    """
    AI 요약 응답 스키마 (Phase 1 통합 버전)

    Phase 2에서 다음과 같이 분리됨:
    - Schema A (Mobile Fast Extract): key_event, bullets, reference_indicators, glossary_terms
    - Schema B (Deep Insight): expected_impact, flow_explanation, trend_insight
    """

    # ===== str 필드 (기본값: "") =====
    key_event: str = Field(
        default="",
        max_length=500,
        description="뉴스 핵심 이벤트 (한 줄 요약, 서술형 1-2문장, 최대 500자)"
    )
    expected_impact: str = Field(
        default="",
        max_length=500,
        description="투자자에게 미칠 영향도 (서술형 1-2문장, 최대 500자)"
    )
    trend_insight: str = Field(
        default="",
        max_length=500,
        description="주가 추세 데이터 기반 분석 (1-2문장, 최대 500자)"
    )
    flow_explanation: str = Field(
        default="",
        max_length=500,
        description="시장 인과관계 흐름 설명 (원인→결과→영향, 최대 500자)"
    )

    # ===== list[str] 필드 (기본값: []) =====
    bullets: list[str] = Field(
        default_factory=list,
        max_items=5,
        description="key_event/expected_impact과 겹치지 않는 보조 정보 (최대 5개)"
    )
    reference_indicators: list[str] = Field(
        default_factory=list,
        max_items=4,
        description="투자자가 확인해야 할 지표 (최대 4개)"
    )

    # ===== list[GlossaryTermModel] 필드 (기본값: []) =====
    glossary_terms: list[GlossaryTermModel] = Field(
        default_factory=list,
        max_items=5,
        description="금융 용어 정의 (최대 5개)"
    )

    # ===== Pydantic v2 설정 =====
    model_config = ConfigDict(
        extra="allow",  # 미래 필드 추가 시 자동 무시 (에러 X)
    )

    # ===== 타입 강제 검증 =====
    @field_validator('key_event', 'expected_impact', 'trend_insight', 'flow_explanation', mode='before')
    @classmethod
    def ensure_str(cls, v):
        """str 타입 강제 (타입 불일치 → ValidationError 발생)"""
        if isinstance(v, str):
            return v
        raise ValueError(f"str 타입이어야 하는데 {type(v).__name__} 수신")

    @field_validator('bullets', 'reference_indicators', mode='before')
    @classmethod
    def ensure_list_of_str(cls, v):
        """list[str] 타입 강제 (비문자열 항목 필터링)"""
        if isinstance(v, list):
            # 각 항목이 str인지 확인, 아니면 필터링
            return [item for item in v if isinstance(item, str)]
        raise ValueError(f"list 타입이어야 하는데 {type(v).__name__} 수신")

    @field_validator('glossary_terms', mode='before')
    @classmethod
    def ensure_glossary_list(cls, v):
        """list[GlossaryTermModel] 타입 강제"""
        if isinstance(v, list):
            valid_terms = []
            for item in v:
                if isinstance(item, dict):
                    try:
                        GlossaryTermModel.model_validate(item)
                        valid_terms.append(item)
                    except Exception:
                        # 검증 실패 항목 제외
                        continue
            return valid_terms
        raise ValueError(f"list 타입이어야 하는데 {type(v).__name__} 수신")
