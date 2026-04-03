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
  const widgetRef = useRef<TradingViewWidgetInstance | null>(null);
  const reactId = useId();
  const containerId = `tv_${symbol.replace(/[^a-zA-Z0-9]/g, "_")}_${reactId.replace(/:/g, "")}`;
  const tvSymbol = toTradingViewSymbol(symbol);

  useEffect(() => {
    let isMounted = true;

    // TradingView 내부 async 에러 억제 — remove() 후에도 async 정리가 이어지다
    // parentNode가 null인 DOM 요소에 접근하는 Uncaught TypeError가 발생하는데,
    // 이 에러가 앱 전체를 크래시시키는 것을 방지한다.
    // 조건을 parentNode null TypeError로 좁혀 다른 TradingView 에러는 계속 관측 가능하게 유지.
    const suppressTVError = (event: ErrorEvent) => {
      const isTVOrigin =
        event.filename?.includes("tv.js") ||
        event.filename?.includes("tradingview");
      const errorMessage =
        event.error instanceof Error ? event.error.message : "";
      const messageCandidates = [event.message, errorMessage].filter(
        (m): m is string => m.length > 0,
      );
      const isKnownParentNodeNullError = messageCandidates.some(
        (m) =>
          m.includes("parentNode") &&
          (m.includes("null") || m.includes("Null")) &&
          m.includes("TypeError"),
      );
      if (isTVOrigin && isKnownParentNodeNullError) {
        event.preventDefault(); // 알려진 정리 단계 에러만 억제 → 앱 크래시 방지
        console.warn("[StockChart] TradingView 내부 parentNode 에러 억제:", event.message);
      }
    };
    window.addEventListener("error", suppressTVError);

    function initWidget() {
      if (!isMounted || !containerRef.current || !window.TradingView) return;
      try {
        widgetRef.current = new window.TradingView.widget({
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
      } catch (e) {
        console.warn("[StockChart] TradingView widget 초기화 실패:", e);
      }
    }

    const cleanup = () => {
      isMounted = false;
      window.removeEventListener("error", suppressTVError);
      if (typeof widgetRef.current?.remove === "function") {
        // remove()가 있으면 TradingView 내부 async 정리 위임
        try { widgetRef.current.remove(); } catch { /* 정리 중 발생하는 에러 무시 */ }
      } else if (containerRef.current) {
        // remove() 미지원 시(초기화 미완료 등) 자식 노드만 제한적으로 제거
        containerRef.current.replaceChildren();
      }
      widgetRef.current = null;
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
      <div id={containerId} ref={containerRef} className="h-[500px]" />
    </div>
  );
}
