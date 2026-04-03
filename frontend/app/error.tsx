"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[App Error Boundary]", error);
  }, [error]);

  const isDev = process.env.NODE_ENV !== "production";

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-200 gap-6 p-8">
      <h2 className="text-xl font-bold text-red-400">오류가 발생했습니다</h2>
      <div className="w-full max-w-2xl bg-slate-900 border border-red-800/50 rounded-xl p-5 space-y-3">
        {/* 개발 환경: 실제 에러 메시지 표시 / 프로덕션: 일반화된 메시지만 표시 (정보 노출 방지) */}
        <p className="text-red-300 font-mono text-sm font-bold">
          {isDev ? error.message : "예기치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
        </p>
        {/* 스택 트레이스와 digest는 개발 환경에서만 노출 (내부 경로/구현 정보 노출 방지) */}
        {isDev && error.stack && (
          <pre className="text-slate-500 font-mono text-[11px] overflow-auto whitespace-pre-wrap leading-relaxed">
            {error.stack}
          </pre>
        )}
        {isDev && error.digest && (
          <p className="text-slate-600 text-[10px] font-mono">digest: {error.digest}</p>
        )}
      </div>
      <button
        onClick={reset}
        className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-bold transition-colors"
      >
        다시 시도
      </button>
    </div>
  );
}
