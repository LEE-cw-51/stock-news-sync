---
name: run-sync
description: 로컬에서 backend/test_run.py를 실행하여 뉴스·주식 데이터 동기화 파이프라인을 검증합니다. (Lambda 배포와 무관, 테스트 전용)
argument-hint: [category: macro|portfolio|watchlist]
---

<!--
  ⚠️ 05번 DevOps 규정 준수:
  이 스킬은 로컬 test_run.py 실행 전용입니다.
  Lambda 배포(aws lambda update-function-code)는 절대 실행하지 않습니다.
  배포는 반드시 GitHub Actions (git push origin main) 경유만 허용됩니다.
-->

`backend` 디렉터리로 이동하여 `python test_run.py $ARGUMENTS`를 실행해줘.

실행 후 결과를 아래 기준으로 요약해줘:

**에러 발생 시:**
- API 키 누락/만료 여부 확인 (GROQ_API_KEY, GEMINI_API_KEY, TAVILY_API_KEY, FIREBASE_*)
- 네트워크 오류 여부 (yfinance, Tavily 연결 실패)
- 모델 쿼터 초과 여부 (429 에러 → 어떤 모델인지 명시)
- 위 3가지 이외의 에러는 스택 트레이스 핵심 1줄 요약

**성공 시:**
- 수집된 시장 지수 개수 (KOSPI, S&P500 등)
- 카테고리별 뉴스 수집 결과 (macro / portfolio / watchlist 종목 수)
- AI 요약 생성 성공/실패 여부
- Firebase RTDB 저장 완료 여부
