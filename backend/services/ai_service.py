import os
import re
import json
import logging
from pathlib import Path
from openai import OpenAI, RateLimitError  # [P5 Fix] RateLimitError 타입 임포트
from dotenv import load_dotenv

try:
    from backend.config.models import MODEL_CONFIG, MAX_TOKENS, TEMPERATURE
except ModuleNotFoundError:
    from config.models import MODEL_CONFIG, MAX_TOKENS, TEMPERATURE

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


def _parse_json_response(raw: str) -> dict | None:
    """
    LLM 응답에서 JSON 객체를 추출합니다.
    - 코드블록(```json ... ```) 제거 후 json.loads() 시도
    - 필드 타입 검증·정규화 후 반환 (타입 오류 시 빈 값으로 강제)
    - 실패 시 None 반환 (호출자가 문자열 폴백 처리)
    """
    # 코드블록 제거: ```json ... ``` 또는 ``` ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
        # 필수 키 검증 (신규 3단 구조 또는 구버전 형식 모두 허용)
        if not (isinstance(parsed, dict) and (
            "bullets" in parsed or "key_event" in parsed
        )):
            return None

        # [Copilot #4] 필드 타입 정규화 — LLM 오출력으로 인한 프론트 런타임 크래시 방지
        # list[str] 필드: 잘못된 타입이면 [] 로 강제
        for list_field in ("bullets", "reference_indicators"):
            v = parsed.get(list_field)
            if not isinstance(v, list):
                parsed[list_field] = []
            else:
                parsed[list_field] = [i for i in v if isinstance(i, str)]

        # glossary_terms: {term: str, definition: str} 형식만 통과
        glossary = parsed.get("glossary_terms")
        if not isinstance(glossary, list):
            parsed["glossary_terms"] = []
        else:
            parsed["glossary_terms"] = [
                g for g in glossary
                if isinstance(g, dict)
                and isinstance(g.get("term"), str)
                and isinstance(g.get("definition"), str)
            ]

        # str 필드: str 아니면 "" 로 강제
        for str_field in ("key_event", "expected_impact", "trend_insight", "flow_explanation"):
            if not isinstance(parsed.get(str_field), str):
                parsed[str_field] = ""

        return parsed
    except (json.JSONDecodeError, ValueError):
        return None


def generate_ai_summary(stock_name: str, context: str, category: str = "watchlist") -> dict | str:
    """
    카테고리별 최적 모델로 AI 브리핑을 생성합니다.
    - 모델 우선순위: backend/config/models.py 에서 설정
    - category: "macro" | "portfolio" | "watchlist"
    - 반환값: JSON 파싱 성공 시 dict, 실패 시 원본 문자열 (하위 호환 폴백)
    """
    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    # 서술형 인사이트 + JSON 전용 출력 시스템 프롬프트
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
      "key_event": "무슨 일이 있었는지 서술형 1-2문장 (수치가 있다면 문장 안에 자연스럽게 포함). 없으면 빈 문자열.",
      "expected_impact": "투자자에게 왜 중요한지, 어떤 영향이 예상되는지 서술형 1-2문장. 없으면 빈 문자열.",
      "reference_indicators": ["투자자가 확인해야 할 지표1", "지표2", "지표3"],
      "bullets": ["key_event/expected_impact와 겹치지 않는 보조 수치·세부정보 1", "보조정보 2"],
      "trend_insight": "주가 추세 데이터 기반 1-2문장 또는 추세 데이터 없음",
      "glossary_terms": [
        {{"term": "용어명", "definition": "한 줄 정의"}}
      ],
      "flow_explanation": "원인 → 결과 → 영향 흐름 1-2문장"
    }}

    - key_event/expected_impact: 제공된 뉴스에서 팩트만. 없으면 "" 반환.
    - reference_indicators: 투자자가 추가로 확인해야 할 경제·기업 지표 2-4개. 없으면 [] 반환.
    - bullets: key_event/expected_impact에서 이미 언급한 내용 제외, 보조 수치·세부 정보만. 없으면 [] 반환.
    - glossary_terms: 투자자가 모를 수 있는 금융·경제 용어 2-3개, 한 줄 정의. 없으면 [] 반환.
    - flow_explanation: 인과관계 흐름 1-2문장. 없으면 "" 반환.
    """

    models = MODEL_CONFIG.get(category, MODEL_CONFIG["watchlist"])

    for model_name in models:
        # 이번 Lambda 실행에서 이미 429가 발생한 모델은 즉시 건너뜀
        if model_name in _quota_exceeded_models:
            logger.info(f"⏭️ {model_name} 할당량 초과 이력 - 건너뜁니다.")
            continue

        try:
            client, api_model = _get_client_and_model(model_name)
            logger.info(f"🤖 [{category.upper()}] AI 분석 시도 중... (모델: {model_name})")

            response = client.chat.completions.create(
                model=api_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )

            # 토큰 제한으로 출력이 잘린 경우 → 다음 모델로 폴백
            if response.choices[0].finish_reason == "length":
                raise Exception("출력이 토큰 제한으로 잘림 - 다음 모델로 전환")

            raw = response.choices[0].message.content or ""

            # JSON 파싱 시도 → 성공 시 dict 반환, 실패 시 원본 문자열 폴백
            parsed = _parse_json_response(raw)
            if parsed is not None:
                logger.info(f"✅ AI 분석 완료 (모델: {model_name}, 형식: JSON)")
                return parsed
            else:
                logger.warning(f"⚠️ {model_name} JSON 파싱 실패 - 문자열 폴백 반환")
                logger.info(f"✅ AI 분석 완료 (모델: {model_name}, 형식: 문자열 폴백)")
                return raw

        except RateLimitError:
            # [P5 Fix] openai SDK의 RateLimitError(HTTP 429)를 타입으로 정확히 감지
            _quota_exceeded_models.add(model_name)
            logger.warning(f"⚠️ {model_name} 할당량 초과(429) - 세션 비활성화 및 다음 모델로 전환합니다.")
            continue

        except Exception as e:
            error_str = str(e)
            # [P5 Fix] Gemini의 RESOURCE_EXHAUSTED는 openai RateLimitError가 아닌
            # 일반 Exception으로 래핑될 수 있어 문자열 체크를 폴백으로 유지
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                _quota_exceeded_models.add(model_name)
                logger.warning(f"⚠️ {model_name} 할당량 초과(429) - 세션 비활성화 및 다음 모델로 전환합니다.")
            else:
                logger.warning(f"⚠️ {model_name} 실패 ({error_str}) -> 다음 모델로 전환합니다.")
            continue

    return "현재 모든 AI 모델의 한도가 초과되었거나 응답할 수 없는 상태입니다."
