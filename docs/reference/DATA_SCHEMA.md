# 데이터 스키마 & AI 모델 라우팅

> 최종 업데이트: 2026-03-23

---

## Firebase Realtime Database 구조 (`/feed/`)

```
/feed/
  market_indices/     # KOSPI, KOSDAQ, S&P500, NASDAQ, USD/KRW, US10Y, BTC
  stock_data/         # 거래량 상위 15개 종목 (US + KR)
  news/
    macro/            # 거시경제 AI 브리핑
    portfolio/        # 포트폴리오 종목 뉴스
    watchlist/        # 관심 종목 뉴스
```

> RTDB 경로 변경 시 반드시 `backend/services/db_service.py` 먼저 검토 (일관성 유지)

---

## Phase 3 DB 전략 (2026-02-25 에이전트 회의 결정)

### 현재 DB 구조

| DB | 용도 | 상태 |
|----|------|------|
| Firebase RTDB | 실시간 시장 데이터 표시 | 유지 (장기) |
| Firestore | 동일 데이터 백업 | 제거 예정 (Phase 3 안정화 후) |
| Supabase PostgreSQL | 주가 히스토리 + 사용자 Watchlist | Phase 3 추가 완료 |

### Supabase 테이블 (Phase 3)

- `stock_history`: OHLCV 60일 데이터
- `watchlist`: 사용자별 관심 종목 (RLS: user_id 기반)
- Connection: Supavisor 포트 6543 (Lambda 연결 풀링, Transaction mode)

### watchlist RLS 정책 목록

| 정책명 | 대상 작업 | 조건 |
|--------|---------|------|
| Users can view own watchlist | SELECT | user_id = auth.uid()::text |
| Users can insert own watchlist | INSERT | user_id = auth.uid()::text |
| Users can delete own watchlist | DELETE | user_id = auth.uid()::text |
| Users can update own watchlist | UPDATE | user_id = auth.uid()::text (USING + WITH CHECK) |

> UPDATE 정책은 2026-03-25 /db-audit 감사에서 누락 발견 후 추가.
> RLS 인증 방식은 2026-03-25 `current_setting('app.user_id', true)` → `auth.uid()` 네이티브 방식으로 교체.

### 이관 원칙

1. **Firebase RTDB**: 실시간 구독 특화, 장기 유지
2. **Firestore**: Supabase로 대체 후 제거 (Phase 3 안정화 후)
3. **Firebase Auth**: Phase 4 이후 Supabase Auth 이관 검토

---

## AI 모델 라우팅 (`backend/config/models.py`)

| 카테고리 | 1순위 | 2순위 | 3순위 |
|---------|------|------|------|
| macro | Gemini 2.5 Pro | Groq GPT-OSS | Gemini Flash |
| portfolio | Groq GPT-OSS | Gemini Pro | Llama 3.1 |
| watchlist | Llama 3.1 | Gemini Flash | Groq GPT-OSS |

- **공통 설정**: `MAX_TOKENS=2500`, `TEMPERATURE=0.2`
- **쿼터 관리**: `_quota_exceeded_models` — 세션 내 재시도 방지

---

## AI 요약 데이터 구조 (`/feed/ai_summaries/`)

> 2026-03-20: 마크다운 문자열 → 구조화 JSON 객체로 전환
> 2026-03-23: `glossary_terms` + `flow_explanation` 필드 추가 (금융 학습 콘텐츠)

### 현재 구조 (JSON 객체)

```json
{
  "macro": {
    "bullets": ["핵심 포인트 1 (수치 포함)", "핵심 포인트 2", "핵심 포인트 3"],
    "market_reaction": {
      "verdict": "호재 | 악재 | 중립",
      "reason": "단기 주가 영향 이유 한 문장"
    },
    "trend_insight": "추세 설명 1-2문장 또는 '추세 데이터 없음'",
    "glossary_terms": [
      {"term": "FOMC", "definition": "미국 연방공개시장위원회 — 금리 결정 기구"}
    ],
    "flow_explanation": "미국 고용지표 호조 → FOMC 금리 동결 기대 약화 → 채권 수익률 상승 → 성장주 하락 압력"
  },
  "portfolio": { ... },
  "watchlist": { ... }
}
```

- `glossary_terms`: 뉴스 내 금융·경제 용어 2-3개. LLM이 생성 못할 경우 `[]`
- `flow_explanation`: 현재 시장 인과관계 흐름 1-2문장. 없으면 `""`
- 두 필드 모두 optional — 구 데이터는 해당 섹션 미표시

### 하위 호환 폴백

Lambda 장애 또는 LLM JSON 파싱 실패 시 기존 마크다운 문자열이 저장될 수 있음.
프론트엔드(`AISummaryCard.tsx`)는 `typeof input === 'string'` 분기로 기존 정규식 파서로 폴백 처리.
