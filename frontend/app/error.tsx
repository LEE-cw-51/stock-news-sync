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

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-200 gap-6 p-8">
      <h2 className="text-xl font-bold text-red-400">오류가 발생했습니다</h2>
      <div className="w-full max-w-2xl bg-slate-900 border border-red-800/50 rounded-xl p-5 space-y-3">
        <p className="text-red-300 font-mono text-sm font-bold">{error.message}</p>
        {error.stack && (
          <pre className="text-slate-500 font-mono text-[11px] overflow-auto whitespace-pre-wrap leading-relaxed">
            {error.stack}
          </pre>
        )}
        {error.digest && (
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
