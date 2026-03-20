"use client";

interface StockChartProps {
  symbol: string;
}

function toTradingViewSymbol(symbol: string): string {
  if (symbol.endsWith(".KS") || symbol.endsWith(".KQ")) {
    return `KRX:${symbol.split(".")[0]}`;
  }
  const exchangeMap: Record<string, string> = {
    NVDA: "NASDAQ", TSLA: "NASDAQ", AAPL: "NASDAQ",
    MSFT: "NASDAQ", GOOGL: "NASDAQ", AMZN: "NASDAQ", META: "NASDAQ",
  };
  return `${exchangeMap[symbol] ?? "NASDAQ"}:${symbol}`;
}

export default function StockChart({ symbol }: StockChartProps) {
  const tvSymbol = toTradingViewSymbol(symbol);
  return (
    <div className="mt-2 rounded-xl overflow-hidden border border-slate-800">
      <iframe
        src={`https://www.tradingview.com/widgetembed/?frameElementId=tv_${symbol}&symbol=${tvSymbol}&interval=D&hidesidetoolbar=1&hidetoptoolbar=1&theme=dark&style=1&timezone=Asia%2FSeoul&locale=kr&toolbarbg=020617&withdateranges=1`}
        width="100%"
        height="220"
        style={{ border: "none", display: "block" }}
        title={`${symbol} chart`}
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>
  );
}
