import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Groq 클라이언트 초기화
_groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=_groq_api_key) if _groq_api_key else None

# [확장성] 2026년 기준 가용 모델 리스트
# 1순위 모델 실패 시 2순위로 자동 전환됩니다.
MODEL_FALLBACK_LIST = [
    "llama-3.1-8b-instant",  # 1순위: 초고속, 효율적 요약
    "openai/gpt-oss-20b"     # 2순위: 모델 사이즈가 커서 더 정교한 분석 가능
]

def generate_ai_summary(stock_name, context):
    """
    뉴스 본문을 바탕으로 분석 리포트를 생성합니다.
    모델 폴백(Fallback) 기능을 통해 API 한도 및 서비스 중단에 대응합니다.
    """
    if not client:
        logger.warning("GROQ_API_KEY가 설정되지 않았습니다. AI 요약을 건너뜁니다.")
        return "AI 서비스 키가 설정되지 않아 요약을 생성할 수 없습니다."

    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    system_prompt = "당신은 냉철한 팩트 기반의 주식 애널리스트입니다."
    
    # Input Token을 아끼기 위해 명확한 출력 양식 지정
    user_prompt = f"""
    [뉴스 데이터]
    {context}

    [임무]
    위 뉴스들을 분석하여 '{stock_name}'에 대한 투자자용 브리핑을 작성하세요.
    
    [출력 양식]
    1. 🔍 **핵심 요약**: 가장 중요한 이슈 3가지를 불렛포인트로 요약 (한국어).
    2. 📊 **시장 반응**: 뉴스가 주가에 미칠 영향(호재/악재/중립)을 한 문장으로.
    """

    for model_name in MODEL_FALLBACK_LIST:
        try:
            logger.info(f"🤖 AI 분석 시도 중... (모델: {model_name})")
            
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2, # 일관성 있는 분석을 위해 낮게 설정
                max_tokens=500,  # Output Token 한도 관리
            )
            
            result = completion.choices[0].message.content
            logger.info(f"✅ AI 분석 완료 (모델: {model_name})")
            return result

        except Exception as e:
            # 429(한도초과) 또는 400(모델 만료) 등의 에러 시 다음 모델 시도
            error_msg = str(e)
            if "429" in error_msg or "model_decommissioned" in error_msg or "400" in error_msg:
                logger.warning(f"⚠️ {model_name} 사용 불가 또는 한도 초과. 다음 모델로 전환합니다.")
                continue 
            else:
                logger.error(f"❌ {model_name} 예외 발생: {e}")
                continue

    return "현재 모든 AI 모델의 한도가 초과되었거나 서비스를 이용할 수 없습니다."