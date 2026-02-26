-- Stock-News-Sync Phase 3: Supabase PostgreSQL 스키마
-- 실행 위치: Supabase Dashboard → SQL Editor

-- ──────────────────────────────────────────
-- 1. stock_history — 60일 OHLCV 주가 히스토리
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_history (
    id          BIGSERIAL PRIMARY KEY,
    symbol      TEXT        NOT NULL,           -- 티커 (예: NVDA, 005930.KS)
    date        DATE        NOT NULL,           -- 거래일
    open        NUMERIC(12, 4),                -- 시가
    high        NUMERIC(12, 4),                -- 고가
    low         NUMERIC(12, 4),                -- 저가
    close       NUMERIC(12, 4),                -- 종가
    volume      BIGINT,                         -- 거래량
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, date)                        -- 중복 방지 (UPSERT 기준)
);

CREATE INDEX IF NOT EXISTS idx_stock_history_symbol_date
    ON stock_history(symbol, date DESC);

-- ──────────────────────────────────────────
-- 2. watchlist — 사용자별 관심 종목 (RLS 적용)
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT        NOT NULL,           -- Firebase Auth uid
    symbol      TEXT        NOT NULL,           -- 티커 (예: AAPL)
    name        TEXT,                           -- 종목명 (예: Apple)
    sector      TEXT,                           -- 섹터 (예: Consumer Electronics)
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)                     -- 사용자별 중복 방지
);

-- RLS (Row Level Security) 활성화
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 watchlist만 조회/수정 가능
CREATE POLICY "Users can view own watchlist"
    ON watchlist FOR SELECT
    USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can insert own watchlist"
    ON watchlist FOR INSERT
    WITH CHECK (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can delete own watchlist"
    ON watchlist FOR DELETE
    USING (user_id = current_setting('app.user_id', true));

-- service_role (Lambda)은 RLS 우회 가능 — 별도 정책 불필요
-- Lambda는 SUPABASE_SERVICE_ROLE_KEY 사용 → 전체 접근 허용
