import logging
import yfinance as yf

logger = logging.getLogger(__name__)

def calc_change(price, prev_close):
    """가격 변동률 계산"""
    if prev_close is None or prev_close == 0:
        return 0.0
    return round(((price - prev_close) / prev_close) * 100, 2)

def get_market_indices(indices_config):
    """지수 및 지표 데이터 수집 (KOSPI, S&P500 등)"""
    updates = {}
    for name, ticker in indices_config.items():
        try:
            t = yf.Ticker(ticker)
            # [P2 Fix] [] 직접 접근 → .get()으로 KeyError 방어
            price = t.fast_info.get('last_price')
            prev = t.fast_info.get('previous_close')
            if price is None:
                logger.warning("fast_info 누락 (%s): last_price", name)
                continue
            updates[name] = {
                "price": round(price, 2),
                "change_percent": calc_change(price, prev)
            }
        except Exception as e:
            logger.warning("Index Error (%s): %s", name, e)
            continue
    return updates

def get_top_volume_stocks(ticker_list, top_n=10):
    """거래량 상위 종목 수집"""
    try:
        tickers = yf.Tickers(" ".join(ticker_list))
        ranking = []
        for symbol in ticker_list:
            try:
                t = tickers.tickers[symbol]
                # [P2 Fix] [] 직접 접근 → .get()으로 KeyError 방어
                price = t.fast_info.get('last_price')
                volume = t.fast_info.get('last_volume')
                prev_close = t.fast_info.get('previous_close')

                if volume is not None and price is not None:
                    ranking.append({
                        "symbol": symbol,
                        "price": price,
                        "volume": volume,
                        "change_percent": calc_change(price, prev_close)
                    })
            except Exception as e:
                logger.warning("Skipping ticker %s: %s", symbol, e)
                continue
        return sorted(ranking, key=lambda x: x['volume'], reverse=True)[:top_n]
    except Exception as e:
        logger.error("Stock Data Error: %s", e)
        return []

def get_stock_history(symbol: str, period: str = "60d") -> list[dict]:
    """종목의 OHLCV 히스토리 수집 (Supabase stock_history 저장용).

    Args:
        symbol: 티커 (예: NVDA, 005930.KS)
        period: yfinance 기간 (기본 60일)

    Returns:
        [{"symbol": str, "date": str, "open": float,
          "high": float, "low": float, "close": float, "volume": int}, ...]
    """
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist.empty:
            logger.warning("히스토리 없음: %s", symbol)
            return []
        records = []
        for date, row in hist.iterrows():
            records.append({
                "symbol": symbol,
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 4) if row["Open"] is not None else None,
                "high": round(float(row["High"]), 4) if row["High"] is not None else None,
                "low": round(float(row["Low"]), 4) if row["Low"] is not None else None,
                "close": round(float(row["Close"]), 4) if row["Close"] is not None else None,
                "volume": int(row["Volume"]) if row["Volume"] is not None else None,
            })
        logger.info("히스토리 수집 완료: %s (%d건)", symbol, len(records))
        return records
    except Exception as e:
        logger.warning("히스토리 수집 실패 (%s): %s", symbol, e)
        return []
