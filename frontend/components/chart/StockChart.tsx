"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, CandlestickSeries, CandlestickData, Time } from "lightweight-charts";
import { supabase } from "@/lib/supabase";
import type { StockHistory } from "@/lib/types";

interface StockChartProps {
  symbol: string;
}

export default function StockChart({ symbol }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 200,
      layout: {
        background: { color: "#020617" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      timeScale: {
        borderColor: "#334155",
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#ef4444",
      downColor: "#3b82f6",
      borderUpColor: "#ef4444",
      borderDownColor: "#3b82f6",
      wickUpColor: "#ef4444",
      wickDownColor: "#3b82f6",
    });

    const fetchData = async () => {
      try {
        const { data, error: sbError } = await supabase
          .from("stock_history")
          .select("date, open, high, low, close, volume")
          .eq("symbol", symbol)
          .order("date", { ascending: true })
          .limit(60);

        if (sbError) throw sbError;

        if (data && data.length > 0) {
          const chartData: CandlestickData[] = (data as StockHistory[]).map(
            (row) => ({
              time: row.date as Time,
              open: row.open,
              high: row.high,
              low: row.low,
              close: row.close,
            })
          );
          candleSeries.setData(chartData);
          chart.timeScale().fitContent();
        } else {
          setError("데이터 없음 (파이프라인 첫 실행 후 표시됩니다)");
        }
      } catch {
        setError("차트 데이터 로드 실패");
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      chart.remove();
    };
  }, [symbol]);

  return (
    <div className="mt-2 rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
      {loading && (
        <div className="h-[200px] flex items-center justify-center text-slate-500 text-xs">
          차트 로딩 중...
        </div>
      )}
      {error && (
        <div className="h-[200px] flex items-center justify-center text-slate-600 text-xs text-center px-4">
          {error}
        </div>
      )}
      <div
        ref={containerRef}
        style={{ display: loading || error ? "none" : "block" }}
      />
    </div>
  );
}
