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
            price = t.fast_info['last_price']
            prev = t.fast_info['previous_close']
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
                price = t.fast_info['last_price']
                volume = t.fast_info['last_volume']
                prev_close = t.fast_info['previous_close']

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