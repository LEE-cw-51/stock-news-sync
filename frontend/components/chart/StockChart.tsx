"use client";

import { useEffect, useRef, useId } from "react";

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

const SCRIPT_ID = "tradingview-widget-script";

interface StockChartProps { symbol: string; }

export default function StockChart({ symbol }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const reactId = useId();
  const containerId = `tv_${symbol.replace(/[^a-zA-Z0-9]/g, "_")}_${reactId.replace(/:/g, "")}`;
  const tvSymbol = toTradingViewSymbol(symbol);

  useEffect(() => {
    let isMounted = true;

    function initWidget() {
      if (!isMounted || !containerRef.current || !window.TradingView) return;
      new window.TradingView.widget({
        autosize: true,
        symbol: tvSymbol,
        interval: "D",
        timezone: "Asia/Seoul",
        theme: "dark",
        style: "1",
        locale: "kr",
        toolbar_bg: "#020617",
        hide_top_toolbar: true,
        hide_side_toolbar: true,
        withdateranges: true,
        container_id: containerId,
      });
    }

    const cleanup = () => {
      isMounted = false;
      if (containerRef.current) containerRef.current.innerHTML = "";
    };

    if (window.TradingView) {
      initWidget();
      return cleanup;
    }

    const existingScript = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (existingScript) {
      existingScript.addEventListener("load", initWidget);
      return () => { existingScript.removeEventListener("load", initWidget); cleanup(); };
    }

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = initWidget;
    document.head.appendChild(script);
    return cleanup;
  }, [containerId, tvSymbol]);

  return (
    <div className="mt-2 rounded-xl overflow-hidden border border-slate-800">
      <div id={containerId} ref={containerRef} style={{ height: 500 }} />
    </div>
  );
}
