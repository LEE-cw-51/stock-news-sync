import os
import logging
import litellm
from dotenv import load_dotenv

from backend.config.models import MODEL_CONFIG, MAX_TOKENS, TEMPERATURE

load_dotenv()

# LiteLLM 내부 디버그 로그 비활성화
litellm.suppress_debug_info = True

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lambda 실행 내 429 초과 모델을 기억 → 같은 세션에서 재시도 방지
_quota_exceeded_models: set = set()


def generate_ai_summary(stock_name: str, context: str, category: str = "watchlist") -> str:
    """
    카테고리별 최적 모델로 AI 브리핑을 생성합니다. (LiteLLM 통합)
    - 모델 우선순위: backend/config/models.py 에서 설정
    - category: "macro" | "portfolio" | "watchlist"
    """
    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    # 환각 방지 시스템 프롬프트
    system_prompt = """당신은 월스트리트의 시니어 주식 애널리스트입니다.
당신의 유일한 목표는 제공된 [뉴스 원문]에서 '팩트'와 '수치'만을 추출하여 투자자에게 객관적인 브리핑을 제공하는 것입니다.
[절대 규칙 - 위반 시 페널티]
1. 환각 금지: 제공된 [뉴스 원문]에 없는 정보나 과거 지식은 절대 지어내지 마십시오.
2. 수치 우선: 주가, 목표가, 실적 퍼센트(%), 날짜 등 숫자가 포함된 문맥은 반드시 요약에 포함하십시오.
3. 간결성: 미사여구를 빼고 건조하고 전문적인 리포트 톤(개조식)으로 작성하십시오.
4. 언어: 반드시 자연스러운 한국어로 출력하십시오."""

    user_prompt = f"""
    [분석 대상 종목]: {stock_name}

    [뉴스 데이터]
    {context}
    [임무]
    위 뉴스들을 분석하여 '{stock_name}'에 대한 투자자용 브리핑을 작성하세요.

    [출력 양식]
    1. 🔍 **핵심 요약**: 가장 중요한 이슈 3가지를 불렛포인트로 요약.
    2. 📊 **시장 반응 예상**: (단기적 관점에서 주가에 미칠 영향을 '호재', '악재', '중립' 중 하나로 명시하고 그 이유를 한 문장으로 서술)
    """

    models = MODEL_CONFIG.get(category, MODEL_CONFIG["watchlist"])

    for model_name in models:
        # 이번 Lambda 실행에서 이미 429가 발생한 모델은 즉시 건너뜀
        if model_name in _quota_exceeded_models:
            logger.info(f"⏭️ {model_name} 할당량 초과 이력 - 건너뜁니다.")
            continue

        try:
            logger.info(f"🤖 [{category.upper()}] AI 분석 시도 중... (모델: {model_name})")

            response = litellm.completion(
                model=model_name,
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

            result = response.choices[0].message.content
            logger.info(f"✅ AI 분석 완료 (모델: {model_name})")
            return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RateLimitError" in error_str:
                _quota_exceeded_models.add(model_name)
                logger.warning(f"⚠️ {model_name} 할당량 초과(429) - 세션 비활성화 및 다음 모델로 전환합니다.")
            else:
                logger.warning(f"⚠️ {model_name} 실패 ({error_str}) -> 다음 모델로 전환합니다.")
            continue

    return "현재 모든 AI 모델의 한도가 초과되었거나 응답할 수 없는 상태입니다."
