import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq 클라이언트 초기화
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_ai_summary(stock_name, context):
    """
    뉴스 본문(context)을 바탕으로 분석 리포트를 생성합니다.
    """
    if not context:
        return "최근 24시간 내 관련된 중요 뉴스 데이터가 없습니다."

    # 프롬프트 설계 (RAG 핵심)
    system_prompt = "당신은 냉철한 팩트 기반의 주식 애널리스트입니다."
    
    user_prompt = f"""
    [뉴스 데이터]
    {context}

    [임무]
    위 뉴스들을 분석하여 '{stock_name}'에 대한 투자자용 브리핑을 작성하세요.
    
    [출력 양식]
    1. 🔍 **핵심 요약**: 가장 중요한 이슈 3가지를 불렛포인트로 요약 (한국어).
    2. 📊 **시장 반응**: 뉴스가 주가에 미칠 영향(호재/악재/중립)을 한 문장으로.

    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # 성능 좋은 모델
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # 사실 기반이므로 창의성(temperature)을 낮춤
            max_tokens= 500
        )
        return completion.choices[0].message.content

    except Exception as e:
        print(f"   ⚠️ Groq 분석 실패: {e}")
        return "AI 서비스 일시 장애로 요약을 생성할 수 없습니다."