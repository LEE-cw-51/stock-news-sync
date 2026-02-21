import os
import logging
from groq import Groq
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. Groq 클라이언트 초기화
_groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=_groq_api_key) if _groq_api_key else None

# 2. Gemini 클라이언트 초기화 (구글 공식 SDK 적용)
_gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=_gemini_api_key) if _gemini_api_key else None

# Lambda 실행 내에서 429(할당량 초과)가 발생한 모델을 기억 → 재시도 방지
_quota_exceeded_models: set = set()


def choose_optimal_models(category: str) -> list:
    """
    카테고리(macro/portfolio/watchlist)별 특성에 맞춰 모델 우선순위를 결정합니다.

    - macro    : 거시경제 인과관계 추론 → 가장 강력한 추론 모델 우선
    - portfolio: 기업별 뉴스 정밀 분석 → 고성능 + 안정적인 할당량
    - watchlist: 트렌드 모니터링      → 초고속 경량 모델로 충분
    """
    if category == "macro":
        logger.info("🌐 [Model Routing] Macro → 추론형 모델 우선 배정")
        return [
            "gemini-2.5-pro",         # 1순위: 복잡한 거시경제 인과관계 추론
            "openai/gpt-oss-20b",     # 2순위: Groq 고성능 폴백
            "gemini-3-flash-preview", # 3순위: 제미나이 플래시
            "llama-3.1-8b-instant",   # 4순위: 최후 폴백
        ]
    elif category == "portfolio":
        logger.info("💼 [Model Routing] Portfolio → 고성능 Groq 모델 우선 배정")
        return [
            "openai/gpt-oss-20b",     # 1순위: 기업별 뉴스 정밀 분석 + Groq이라 할당량 부담 없음
            "gemini-2.5-pro",         # 2순위: 제미나이 프로 폴백
            "llama-3.1-8b-instant",   # 3순위: 초고속 Llama
            "gemini-3-flash-preview", # 4순위: 제미나이 플래시
        ]
    else:  # watchlist
        logger.info("⭐ [Model Routing] Watchlist → 초고속 경량 모델 우선 배정")
        return [
            "llama-3.1-8b-instant",   # 1순위: 트렌드 모니터링엔 초고속 경량 모델로 충분
            "gemini-3-flash-preview", # 2순위: 제미나이 플래시 폴백
            "openai/gpt-oss-20b",     # 3순위: Groq 고성능
            "gemini-2.5-pro",         # 4순위: 최후 폴백
        ]


def generate_ai_summary(stock_name, context, category: str = "watchlist"):
    """
    카테고리별 최적 모델 라우팅 및 폴백을 통해 브리핑을 생성합니다.
    category: "macro" | "portfolio" | "watchlist"
    """
    if not groq_client and not gemini_client:
        return "API 키(Groq 또는 Gemini)가 설정되지 않아 요약을 생성할 수 없습니다."
    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    # 환각(거짓 정보)을 막는 강력한 시스템 프롬프트
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

    # 카테고리에 맞춰 4개 모델의 최적 순위 리스트를 받아옴
    dynamic_fallback_list = choose_optimal_models(category)

    for model_name in dynamic_fallback_list:
        # 이번 Lambda 실행 중 이미 429가 발생한 모델은 즉시 건너뜀
        if model_name in _quota_exceeded_models:
            logger.info(f"⏭️ {model_name} 할당량 초과 이력 있음 - 건너뜁니다.")
            continue

        try:
            logger.info(f"🤖 AI 분석 시도 중... (모델: {model_name})")

            # [Gemini 모델 처리 로직]
            if "gemini" in model_name:
                if not gemini_client:
                    raise Exception("GEMINI_API_KEY가 없습니다.")

                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.2,
                        max_output_tokens=1000
                    )
                )

                # 토큰 제한으로 인한 출력 잘림 감지 → 다음 모델로 폴백
                if response.candidates and response.candidates[0].finish_reason == types.FinishReason.LENGTH:
                    raise Exception("Output truncated due to token limit (LENGTH) - trying next model")

                result = response.text

            # [Groq 모델 처리 로직]
            else:
                if not groq_client:
                    raise Exception("GROQ_API_KEY가 없습니다.")

                completion = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1000,
                )

                # 토큰 제한으로 인한 출력 잘림 감지 → 다음 모델로 폴백
                if completion.choices[0].finish_reason == "length":
                    raise Exception("Output truncated due to token limit (length) - trying next model")

                result = completion.choices[0].message.content

            logger.info(f"✅ AI 분석 완료 (사용한 모델: {model_name})")
            return result

        except Exception as e:
            error_str = str(e)
            # 429 할당량 초과 → 세션 내 영구 비활성화 (이후 호출에서 즉시 스킵)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                _quota_exceeded_models.add(model_name)
                logger.warning(f"⚠️ {model_name} 할당량 초과(429) - 세션 비활성화 및 다음 모델로 전환합니다.")
            else:
                logger.warning(f"⚠️ {model_name} 실패 ({error_str}) -> 다음 모델로 전환합니다.")
            continue

    return "현재 모든 AI 모델(4개)의 한도가 초과되었거나 응답할 수 없는 상태입니다."
