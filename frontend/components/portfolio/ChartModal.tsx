"use client";

import { useEffect, useRef } from "react";
import StockChart from "@/components/chart/StockChart";
import type { StockData } from "@/lib/types";

interface ChartModalProps {
  stock: StockData;
  onClose: () => void;
}

export default function ChartModal({ stock, onClose }: ChartModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<Element | null>(null);

  useEffect(() => {
    // 열릴 때: 이전 포커스 저장 + 닫기 버튼으로 초기 포커스
    previousFocusRef.current = document.activeElement;
    closeButtonRef.current?.focus();

    // ESC 키 닫기
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);

    return () => {
      window.removeEventListener("keydown", onKey);
      // 닫힐 때: 이전 포커스 복원
      (previousFocusRef.current as HTMLElement | null)?.focus?.();
    };
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`chart-title-${stock.symbol}`}
      className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center pt-20 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl max-h-[90vh] bg-slate-900 rounded-2xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-4 py-3 border-b border-slate-800">
          <span
            id={`chart-title-${stock.symbol}`}
            className="text-sm font-bold text-slate-300"
          >
            {stock.name} ({stock.symbol})
          </span>
          <button
            type="button"
            ref={closeButtonRef}
            onClick={onClose}
            className="text-slate-500 hover:text-slate-300 text-xl leading-none"
            aria-label="차트 닫기"
          >
            ×
          </button>
        </div>
        <StockChart symbol={stock.symbol} />
      </div>
    </div>
  );
}
