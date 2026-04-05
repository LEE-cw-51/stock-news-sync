import os
import re
import json
import logging
from pathlib import Path
from openai import OpenAI, RateLimitError  # [P5 Fix] RateLimitError 타입 임포트
from dotenv import load_dotenv
from pydantic import ValidationError

try:
    from backend.config.models import MODEL_CONFIG, SLM_MODEL_CONFIG, MAX_TOKENS, SLM_MAX_TOKENS, TEMPERATURE
    from backend.schemas.ai_schemas import (
        AISummarySchema, AISummaryFastSchema, AISummaryDeepSchema, GlossaryTermModel
    )
except ModuleNotFoundError:
    from config.models import MODEL_CONFIG, SLM_MODEL_CONFIG, MAX_TOKENS, SLM_MAX_TOKENS, TEMPERATURE
    from schemas.ai_schemas import (
        AISummarySchema, AISummaryFastSchema, AISummaryDeepSchema, GlossaryTermModel
    )

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# OpenAI 호환 클라이언트 초기화
# Groq와 Gemini 모두 OpenAI API 형식을 지원하므로 base_url만 달리해 통합합니다.
# =============================================================================
_GROQ_CLIENT = OpenAI(
    api_key=os.getenv("GROQ_API_KEY", ""),
    base_url="https://api.groq.com/openai/v1",
) if os.getenv("GROQ_API_KEY") else None

_GEMINI_CLIENT = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY", ""),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
) if os.getenv("GEMINI_API_KEY") else None

if not _GROQ_CLIENT:
    logger.error("❌ GROQ_API_KEY가 설정되지 않았습니다.")
if not _GEMINI_CLIENT:
    logger.error("❌ GEMINI_API_KEY가 설정되지 않았습니다.")

# Lambda 실행 내 429 초과 모델을 기억 → 같은 세션에서 재시도 방지
_quota_exceeded_models: set = set()


def _get_client_and_model(model_name: str):
    """
    모델 이름의 prefix로 클라이언트와 실제 API 모델명을 분리합니다.
      "groq/<model>"   → _GROQ_CLIENT   + "<model>"
      "gemini/<model>" → _GEMINI_CLIENT + "<model>"
    """
    if model_name.startswith("groq/"):
        if not _GROQ_CLIENT:
            raise Exception("GROQ_API_KEY가 없습니다.")
        return _GROQ_CLIENT, model_name[len("groq/"):]

    if model_name.startswith("gemini/"):
        if not _GEMINI_CLIENT:
            raise Exception("GEMINI_API_KEY가 없습니다.")
        return _GEMINI_CLIENT, model_name[len("gemini/"):]

    raise ValueError(f"알 수 없는 모델 prefix: {model_name}")


def _call_llm(model_name: str, messages: list, max_tokens: int) -> str | None:
    """
    단일 LLM 호출 공통 함수.
    - 429/할당량 초과 시 _quota_exceeded_models에 기록 후 None 반환
    - 토큰 잘림(finish_reason=length) 시 None 반환
    - 성공 시 응답 문자열 반환
    """
    if model_name in _quota_exceeded_models:
        return None

    try:
        client, api_model = _get_client_and_model(model_name)
        response = client.chat.completions.create(
            model=api_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
        )
        if response.choices[0].finish_reason == "length":
            logger.warning("⚠️ %s 토큰 잘림(length) → 건너뜁니다.", model_name)
            return None
        return response.choices[0].message.content or ""

    except RateLimitError:
        _quota_exceeded_models.add(model_name)
        logger.warning("⚠️ %s 할당량 초과(429) - 세션 비활성화.", model_name)
        return None

    except Exception as e:
        error_str = str(e)
        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            _quota_exceeded_models.add(model_name)
            logger.warning("⚠️ %s 할당량 초과(429) - 세션 비활성화.", model_name)
        else:
            logger.warning("⚠️ %s 실패 (%s)", model_name, error_str[:80])
        return None


def _parse_fast_schema(raw: str) -> dict | None:
    """Schema A (AISummaryFastSchema) 파싱 — SLM 응답 전용."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
    try:
        raw_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("⚠️ AISummaryFastSchema JSON 디코딩 실패: %s", e)
        return None

    try:
        schema = AISummaryFastSchema.model_validate(raw_dict)
        return schema.model_dump()
    except ValidationError:
        # JSON 파싱은 성공했지만 스키마가 맞지 않는 경우에만 부분 복구
        # 스키마 제약(max_length/max_items)을 수동으로 적용
        result: dict = {}
        for field_name in AISummaryFastSchema.model_fields:
            val = raw_dict.get(field_name)
            if field_name == 'key_event':
                result[field_name] = (val[:500] if isinstance(val, str) else "")
            elif field_name == 'bullets':
                result[field_name] = [v for v in (val or []) if isinstance(v, str)][:5]
            elif field_name == 'reference_indicators':
                result[field_name] = [v for v in (val or []) if isinstance(v, str)][:4]
            elif field_name == 'glossary_terms':
                result[field_name] = [
                    item for item in (val or [])
                    if isinstance(item, dict)
                    and isinstance(item.get("term"), str)
                    and isinstance(item.get("definition"), str)
                ][:5]
        return result


def _parse_deep_schema(raw: str) -> dict | None:
    """Schema B (AISummaryDeepSchema) 파싱 — LLM Thinker 응답 전용."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
    try:
        raw_dict = json.loads(cleaned)
    except json.JSONDecodeError:
        raw_dict = {}

    try:
        schema = AISummaryDeepSchema.model_validate(raw_dict)
        return schema.model_dump()
    except ValidationError:
        result: dict = {}
        for field_name in AISummaryDeepSchema.model_fields:
            val = raw_dict.get(field_name)
            result[field_name] = val[:500] if isinstance(val, str) else ""
        return result


def _generate_fast_extract(
    stock_name: str, context: str, category: str
) -> dict | None:
    """
    Step 1 — SLM Worker: Schema A (key_event, bullets, reference_indicators, glossary_terms) 빠른 추출.
    - SLM_MODEL_CONFIG의 빠른 모델 사용
    - 실패 시 None 반환 → 호출자가 단일 폴백으로 전환
    """
    system_prompt = """당신은 한국어 금융 뉴스 팩트 추출 엔진입니다.
모바일 투자자에게 핵심 정보를 1초 내에 정확한 JSON으로 전달하는 것이 유일한 임무입니다.

[절대 규칙]
1. 환각 금지: 제공된 뉴스 원문에 없는 정보는 절대 작성하지 마십시오.
2. 수치 정확성: 퍼센트·금액·날짜는 원문 그대로 인용하십시오. 추정값 사용 금지.
3. 언어: 반드시 한국어로 출력하십시오.
4. JSON ONLY: 마크다운·코드블록·설명 텍스트 없이 순수 JSON만 출력하십시오.

[추출 우선순위]
- key_event: 가장 중요한 단일 이벤트를 서술형 1-2문장으로 (기업명·수치 포함)
- bullets: key_event와 겹치지 않는 보조 수치·세부 사실만 (매출 증감률, 경쟁사 동향 등)
- reference_indicators: 다음 거래일에 투자자가 확인해야 할 구체적 지표 (외국인 순매수, 환율 등)
- glossary_terms: 일반 투자자가 모를 수 있는 전문 용어만 선별 (PER, EPS, 레포금리 등)

[스키마 제약 — 위반 시 응답 거부됨]
- key_event: 최대 500자 (서술형 1-2문장)
- bullets: 최대 5개 항목 (key_event 중복 금지)
- reference_indicators: 최대 4개 항목
- glossary_terms: 최대 5개 항목 (term ≤50자, definition ≤200자)"""

    user_prompt = f"""
[분석 대상]: {stock_name}

[뉴스 데이터]
{context}

[임무] 아래 4개 필드만 추출하여 JSON으로 반환하세요.

[출력 형식 - 순수 JSON만]
{{
  "key_event": "무슨 일이 있었는지 서술형 1-2문장 (최대 500자). 없으면 빈 문자열.",
  "bullets": ["key_event와 겹치지 않는 보조 수치·세부정보 (최대 5개)"],
  "reference_indicators": ["투자자가 확인해야 할 지표 (최대 4개)"],
  "glossary_terms": [{{"term": "용어명(최대 50자)", "definition": "한 줄 정의(최대 200자)"}}]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for model_name in SLM_MODEL_CONFIG.get(category, SLM_MODEL_CONFIG["watchlist"]):
        logger.info("⚡ [SLM Worker] Schema A 추출 시도 (모델: %s)", model_name)
        raw = _call_llm(model_name, messages, SLM_MAX_TOKENS)
        if raw is None:
            continue
        parsed = _parse_fast_schema(raw)
        if parsed:
            logger.info("✅ [SLM Worker] Schema A 추출 완료 (모델: %s)", model_name)
            return parsed

    logger.warning("⚠️ [SLM Worker] 모든 모델 실패 → 단일 폴백으로 전환")
    return None


def _generate_deep_insight(
    stock_name: str, context: str, fast_result: dict, category: str
) -> dict:
    """
    Step 2 — LLM Thinker: Schema B (expected_impact, flow_explanation, trend_insight) 심층 분석.
    - Step 1 결과(fast_result)를 컨텍스트로 받아 심층 추론 수행
    - 실패 시 기본값 dict 반환 (빈 문자열)
    """
    key_event_summary = fast_result.get("key_event", "")

    system_prompt = """당신은 투자자에게 뉴스 기반 심층 인사이트를 제공하는 시니어 애널리스트입니다.
[절대 규칙]
1. 환각 금지: 제공된 뉴스 원문에 없는 정보는 절대 작성하지 마십시오.
2. 서술형 우선: 반드시 완전한 문장으로 작성하세요.
3. 언어: 반드시 한국어로 출력하십시오.
4. JSON ONLY: 마크다운·코드블록 없이 순수 JSON만 출력하십시오."""

    user_prompt = f"""
[분석 대상]: {stock_name}

[뉴스 데이터]
{context}

[1단계 팩트 요약 (참고용)]
{key_event_summary}

[임무] 위 뉴스와 팩트 요약을 바탕으로 아래 3개 심층 분석 필드를 JSON으로 작성하세요.

[출력 형식 - 순수 JSON만]
{{
  "expected_impact": "투자자에게 왜 중요한지, 어떤 영향이 예상되는지 서술형 1-2문장 (최대 500자). 없으면 빈 문자열.",
  "flow_explanation": "원인 → 결과 → 영향 흐름 1-2문장 (최대 500자). 없으면 빈 문자열.",
  "trend_insight": "주가 추세 데이터 기반 1-2문장 (최대 500자). 없으면 빈 문자열."
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # LLM Thinker는 기존 MODEL_CONFIG 사용 (고성능 모델 우선)
    for model_name in MODEL_CONFIG.get(category, MODEL_CONFIG["watchlist"]):
        logger.info("🧠 [LLM Thinker] Schema B 분석 시도 (모델: %s)", model_name)
        raw = _call_llm(model_name, messages, MAX_TOKENS)
        if raw is None:
            continue
        parsed = _parse_deep_schema(raw)
        if parsed:
            logger.info("✅ [LLM Thinker] Schema B 분석 완료 (모델: %s)", model_name)
            return parsed

    logger.warning("⚠️ [LLM Thinker] 모든 모델 실패 → Schema B 기본값 반환")
    return {"expected_impact": "", "flow_explanation": "", "trend_insight": ""}


def _parse_with_pydantic(raw: str) -> dict | None:
    """
    LLM 응답을 Pydantic으로 파싱합니다.

    전략:
    1. JSON 파싱 실패 → None 반환 → 호출자(_fallback_single_call)가 원본 문자열로 폴백
    2. JSON 성공 + Pydantic 검증 성공 → 완전한 dict 반환
    3. JSON 성공 + ValidationError → 부분 파싱: 필드별 독립 복구 후 dict 반환

    반환:
    - None: JSON 파싱 자체가 불가한 경우 (비-JSON 응답)
    - dict: JSON 파싱 성공 시 (검증 성공 또는 부분 복구)
    """

    # Step 1: 코드블록 정규화
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()

    # Step 2: JSON 파싱 (실패 시 None 반환 → 호출자가 원본 문자열 폴백 처리)
    try:
        raw_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("⚠️ JSON 파싱 실패: %s → None 반환", e)
        return None

    # Step 3: Pydantic 검증 (필드별 독립 검증)
    try:
        schema = AISummarySchema.model_validate(raw_dict)
        logger.debug("✅ Pydantic 검증 성공: %d 필드", len(schema.model_dump()))
        return schema.model_dump()

    except ValidationError as e:
        # 부분 파싱: 각 필드를 개별적으로 재검증
        logger.warning("⚠️ Pydantic 검증 실패: %d 필드 오류 → 부분 파싱 시도", e.error_count())

        validated_data = {}
        for field_name, field_info in AISummarySchema.model_fields.items():
            field_value = raw_dict.get(field_name)

            try:
                # 필드별 검증 (간단 버전: Pydantic 전체 검증보다 가볍게)
                if field_name == 'bullets':
                    validated_data[field_name] = (
                        [v for v in field_value if isinstance(v, str)][:5]
                        if isinstance(field_value, list) else []
                    )

                elif field_name == 'reference_indicators':
                    validated_data[field_name] = (
                        [v for v in field_value if isinstance(v, str)][:4]
                        if isinstance(field_value, list) else []
                    )

                elif field_name == 'glossary_terms':
                    if isinstance(field_value, list):
                        valid_terms = []
                        for item in field_value:
                            try:
                                GlossaryTermModel.model_validate(item)
                                valid_terms.append(item)
                            except ValidationError:
                                continue
                        validated_data[field_name] = valid_terms[:5]
                    else:
                        validated_data[field_name] = []

                else:  # str 필드 (key_event, expected_impact, trend_insight, flow_explanation)
                    if isinstance(field_value, str):
                        validated_data[field_name] = field_value[:500]
                    else:
                        validated_data[field_name] = ""

            except Exception as ex:
                # 예상 외 오류 → 기본값 사용
                logger.warning("⚠️ %s 필드 복구 실패: %s", field_name, ex)
                default_value = field_info.get_default(call_default_factory=True)
                if default_value is None:
                    default_value = [] if 'list' in str(field_info.annotation) else ""
                validated_data[field_name] = default_value

        logger.info("✅ 부분 파싱 완료: %d 필드 복원", len(validated_data))
        return validated_data


def _fallback_single_call(
    stock_name: str, context: str, category: str
) -> dict | str:
    """
    폴백 단일 호출 — Step 1 실패 시 기존 방식으로 7개 필드 한 번에 생성.
    Phase 1 방식 그대로 유지 (하위 호환성 보장).
    """
    system_prompt = """당신은 투자자에게 뉴스 기반 인사이트를 전달하는 시니어 애널리스트입니다.
제공된 [뉴스 원문]을 바탕으로 투자자가 상황을 즉시 이해할 수 있는 서술형 분석을 작성하세요.
[절대 규칙]
1. 환각 금지: 제공된 [뉴스 원문]에 없는 정보는 절대 작성하지 마십시오.
2. 서술형 우선: key_event·expected_impact는 반드시 완전한 문장으로 작성하세요. 수치는 문장 맥락 안에 자연스럽게 포함하되, 수치만 나열하지 마십시오.
3. 언어: 반드시 자연스러운 한국어로 출력하십시오.
4. JSON ONLY: 반드시 아래 JSON 형식으로만 응답하십시오. 마크다운, 코드블록, 설명 텍스트 없이 순수 JSON만 출력하십시오.
[출력 필드 역할 정의 - 중복 방지]
- key_event: 무슨 일이 있었는지 서술형 1-2문장 (관련 수치가 있다면 문장 안에 자연스럽게 포함)
- expected_impact: 투자자에게 왜 중요한지, 어떤 영향이 예상되는지 서술형 1-2문장
- bullets: key_event/expected_impact에서 다루지 않은 세부 보조 수치·부연 정보만 (최대 3개)
  ※ key_event/expected_impact와 내용이 겹치는 bullets는 작성하지 말 것"""

    user_prompt = f"""
    [분석 대상 종목]: {stock_name}

    [뉴스 데이터]
    {context}
    [임무]
    위 뉴스들을 분석하여 '{stock_name}'에 대한 투자자용 브리핑을 다음 JSON 형식으로 작성하세요.

    [출력 형식 - 순수 JSON만, 코드블록 없이]
    {{
      "key_event": "무슨 일이 있었는지 서술형 1-2문장 (최대 500자). 없으면 빈 문자열.",
      "expected_impact": "투자자에게 왜 중요한지, 어떤 영향이 예상되는지 서술형 1-2문장 (최대 500자). 없으면 빈 문자열.",
      "reference_indicators": ["투자자가 확인해야 할 지표1", "지표2", "지표3"],
      "bullets": ["key_event/expected_impact와 겹치지 않는 보조 수치·세부정보 1", "보조정보 2"],
      "trend_insight": "주가 추세 데이터 기반 1-2문장 (최대 500자) 또는 추세 데이터 없음",
      "glossary_terms": [
        {{"term": "용어명 (최대 50자)", "definition": "한 줄 정의 (최대 200자)"}}
      ],
      "flow_explanation": "원인 → 결과 → 영향 흐름 1-2문장 (최대 500자)"
    }}

    [필드별 제약 조건 - PYDANTIC 검증]
    - key_event: 최대 500자, 서술형 1-2문장. 없으면 "" 반환.
    - expected_impact: 최대 500자, 서술형 1-2문장. 없으면 "" 반환.
    - reference_indicators: 최대 4개 항목. 2-4개 지표 권장. 없으면 [] 반환.
    - bullets: 최대 5개 항목. key_event/expected_impact에서 이미 언급한 내용 제외, 보조 수치·세부 정보만. 없으면 [] 반환.
    - trend_insight: 최대 500자. 주가 추세 기반 1-2문장. 없으면 "" 반환.
    - glossary_terms: 최대 5개 항목, 각 term(최대 50자) + definition(최대 200자). 금융 용어 2-3개 권장. 없으면 [] 반환.
    - flow_explanation: 최대 500자. 인과관계 흐름 1-2문장. 없으면 "" 반환.

    [중요] 각 필드가 지정된 최대 길이·개수를 초과하면 안 됩니다!
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for model_name in MODEL_CONFIG.get(category, MODEL_CONFIG["watchlist"]):
        logger.info("🤖 [폴백 단일호출] AI 분석 시도 (모델: %s)", model_name)
        raw = _call_llm(model_name, messages, MAX_TOKENS)
        if raw is None:
            continue
        parsed = _parse_with_pydantic(raw)
        if parsed:
            logger.info("✅ [폴백] AI 분석 완료 (모델: %s)", model_name)
            return parsed
        logger.error("❌ [폴백] Pydantic 파싱 실패 - 원본 문자열 반환")
        return raw

    return "현재 모든 AI 모델의 한도가 초과되었거나 응답할 수 없는 상태입니다."


def generate_ai_summary(stock_name: str, context: str, category: str = "watchlist") -> dict | str:
    """
    카테고리별 최적 모델로 AI 브리핑을 생성합니다. (Phase 2: Router-Worker 구조)

    흐름:
      Step 1 (SLM Worker)  → Schema A (key_event, bullets, reference_indicators, glossary_terms) 빠른 추출
      Step 2 (LLM Thinker) → Schema B (expected_impact, flow_explanation, trend_insight) 심층 분석
      두 결과를 병합하여 반환.

    폴백:
      Step 1 실패 시 → 기존 단일 호출 방식(_fallback_single_call)으로 7개 필드 한 번에 생성.

    - category: "macro" | "portfolio" | "watchlist"
    - 반환값: dict (JSON) 또는 str (완전 실패 시 메시지)
    """
    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    logger.info("🚀 [%s] Router-Worker AI 분석 시작: %s", category.upper(), stock_name)

    # Step 1: SLM Worker — Schema A 빠른 추출
    fast_result = _generate_fast_extract(stock_name, context, category)

    if fast_result is None:
        # Step 1 실패 → 기존 단일 호출 방식으로 폴백
        logger.warning("⚠️ Step 1 실패 → 단일 폴백 호출로 전환")
        return _fallback_single_call(stock_name, context, category)

    # Step 2: LLM Thinker — Schema B 심층 분석 (Step 1 결과 활용)
    # 확장 포인트: 향후 expected_impact·trend_insight 등 특정 필드를
    #   전용 고성능 모델(예: gemini-2.5-pro)로 라우팅하려면 이 지점에서 분기 추가
    deep_result = _generate_deep_insight(stock_name, context, fast_result, category)

    # Schema A + Schema B 병합 → 최종 7개 필드 dict
    merged = {**fast_result, **deep_result}
    logger.info("✅ [%s] Router-Worker 완료: %s (%d 필드)", category.upper(), stock_name, len(merged))
    return merged
