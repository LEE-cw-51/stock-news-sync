import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 호환성 모드로 Groq 연결
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

def generate_summary(category, news_items):
    """
    뉴스 리스트를 받아 Groq(Llama 3) 모델을 통해 3줄 요약을 생성합니다.
    """
    if not news_items:
        return f"현재 {category} 관련 주요 뉴스가 없습니다."

    # 뉴스 제목 상위 5개 추출
    news_text = "\n".join([f"- {item['title']}" for item in news_items[:5]])

    system_prompt = f"""
    당신은 '{category}' 전문 금융 전략가입니다.
    제공된 뉴스 헤드라인들을 분석하여 투자자가 반드시 알아야 할 핵심을 요약하세요.
    
    [규칙]
    1. 반드시 한국어로 답변할 것.
    2. 딱 3개의 문장(BULLET POINTS)으로 요약할 것.
    3. '~함', '~임'과 같은 명사형 종결 어미를 사용할 것.
    4. 투자 조언은 배제하고 시장의 팩트와 흐름 위주로 전달할 것.
    """

    user_prompt = f"다음은 수집된 뉴스입니다:\n{news_text}\n\n이 뉴스들을 {category} 관점에서 3줄 브리핑해줘."

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Groq Error ({category}): {e}")
        return "데이터를 요약하는 중 오류가 발생했습니다."