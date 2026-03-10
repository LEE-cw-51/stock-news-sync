# =============================================================================
# AI 모델 설정 파일
# 모델 추가/변경/순서 조정은 이 파일만 수정하면 됩니다.
#
# 모델명 규칙 (OpenAI 호환 SDK, prefix로 클라이언트 분기):
#   Gemini  → "gemini/<model-id>"   → Google Gemini API
#   Groq    → "groq/<model-id>"    → Groq API
# =============================================================================

MODEL_CONFIG: dict[str, list[str]] = {

    # 거시경제: 복잡한 인과관계 추론 → 가장 강력한 추론 모델 우선
    "macro": [
        "gemini/gemini-2.5-pro",          # 1순위: 복잡한 거시경제 추론 (2 RPM)
        "groq/openai/gpt-oss-20b",        # 2순위: Groq 고성능 폴백
        "gemini/gemini-2.5-flash",        # 3순위: 제미나이 플래시 (10 RPM, 250 RPD)
        "groq/llama-3.1-8b-instant",      # 4순위: 최후 폴백
    ],

    # 포트폴리오: 기업별 정밀 분석 → 고성능 + 할당량 안정적인 Groq 우선
    "portfolio": [
        "groq/openai/gpt-oss-20b",        # 1순위: 정밀 분석 + Groq이라 할당량 부담 없음
        "gemini/gemini-2.5-pro",          # 2순위: 제미나이 프로 폴백
        "groq/llama-3.1-8b-instant",      # 3순위: 초고속 Llama
        "gemini/gemini-2.5-flash",        # 4순위: 플래시 폴백
    ],

    # 관심종목: 트렌드 모니터링 → 초고속 경량 모델로 충분
    "watchlist": [
        "groq/llama-3.1-8b-instant",      # 1순위: 트렌드 모니터링엔 경량 모델로 충분
        "gemini/gemini-2.5-flash",        # 2순위: 플래시 폴백 (10 RPM)
        "groq/openai/gpt-oss-20b",        # 3순위: Groq 고성능
        "gemini/gemini-2.5-flash-lite",   # 4순위: 최고 일일 할당량 (1000 RPD)
    ],

}

# 출력 토큰 한도 (모든 모델 공통)
MAX_TOKENS: int = 1500

# 창의성 억제 (팩트 기반 분석을 위해 낮게 설정)
TEMPERATURE: float = 0.2
