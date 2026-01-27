"use client";

import { useEffect, useState } from "react";
import { db } from "@/lib/firebase";
import { ref, onValue } from "firebase/database";
import { Activity, Zap } from "lucide-react";

const getChangeColor = (value: number) => {
  if (value > 0) return "text-red-500";
  if (value < 0) return "text-blue-500";
  return "text-slate-500";
};

export default function Dashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const rootRef = ref(db, "/");
    const unsubscribe = onValue(rootRef, (snapshot) => {
      if (snapshot.exists()) setData(snapshot.val());
    });
    return () => unsubscribe();
  }, []);

  if (!data) return (
    <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
      <div className="flex flex-col items-center gap-4">
        <Activity className="animate-spin text-blue-500" size={48} />
        <p className="font-mono tracking-widest text-sm text-slate-400">CONNECTING TO ENGINE...</p>
      </div>
    </div>
  );

  const allStocks = Object.entries(data.sync_feed || {}).map(([symbol, item]: any) => ({
    symbol: symbol.replace("_", "."),
    ...item
  }));
  
  // 거래량 순 정렬
  const usStocks = allStocks.filter(s => s.country === 'US').sort((a, b) => b.volume - a.volume);
  const krStocks = allStocks.filter(s => s.country === 'KR').sort((a, b) => b.volume - a.volume);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-200 p-4 font-sans selection:bg-blue-500/30">
      
      {/* 1. 상단 지표 바 */}
      <div className="flex gap-4 overflow-x-auto pb-4 mb-4 border-b border-slate-800 no-scrollbar">
        {Object.entries(data.key_indicators || {}).map(([name, val]: any) => (
          <div key={name} className="flex items-center gap-3 whitespace-nowrap bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{name}</span>
            <span className="font-mono font-bold text-sm text-blue-100">{val.price.toLocaleString()}</span>
            <span className={`text-[10px] font-bold ${getChangeColor(val.change_percent)}`}>
              {val.change_percent > 0 ? "+" : ""}{val.change_percent}%
            </span>
          </div>
        ))}
      </div>

      {/* 2. 주요 지수 */}
      <div className="flex gap-4 overflow-x-auto pb-6 mb-8 no-scrollbar">
        {[
          ...Object.entries(data.market_indices?.global || {}),
          ...Object.entries(data.market_indices?.domestic || {})
        ].map(([name, val]: any) => (
          <div key={name} className="flex-1 min-w-[160px] bg-gradient-to-br from-slate-900 to-slate-900/50 p-4 rounded-xl border border-slate-700/50 shadow-lg hover:border-slate-600 transition-all">
            <div className="text-[10px] font-bold text-slate-400 uppercase mb-2">{name.replace("_", " ")}</div>
            <div className="flex justify-between items-end">
              <span className="text-xl font-bold tracking-tight text-white">{val.price.toLocaleString()}</span>
              <span className={`text-xs font-bold ${getChangeColor(val.change_percent)}`}>
                {val.change_percent > 0 ? "▲" : "▼"} {Math.abs(val.change_percent)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* 3. 미국 시장 섹션 */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
             <div className="w-1 h-6 bg-indigo-500 rounded-full"></div>
             <h2 className="text-xl font-black italic tracking-tighter uppercase text-slate-100">United States</h2>
          </div>
          <div className="flex flex-col gap-4">
            {usStocks.map((stock) => (
              <div key={stock.symbol} className="bg-slate-900 p-5 rounded-xl border border-slate-800 hover:border-indigo-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    {/* ⭐️ 이름(큰글씨) + 티커(작은글씨) 구조 */}
                    <div className="text-lg font-bold text-indigo-100 leading-tight">
                        {stock.company_name || stock.symbol} 
                    </div>
                    <div className="text-xs font-bold text-slate-500 mt-1">{stock.symbol}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-lg text-white">{stock.price.toLocaleString()}</div>
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-950 ${getChangeColor(stock.change_percent)}`}>
                      {stock.change_percent > 0 ? "+" : ""}{stock.change_percent}%
                    </span>
                  </div>
                </div>
                
                {/* 뉴스 영역 */}
                <div className="relative pl-3 border-l-2 border-slate-700 hover:border-indigo-500 transition-colors">
                    <div className="text-[9px] text-slate-500 font-bold uppercase mb-1 flex items-center gap-1">
                        <Zap size={10} className="text-yellow-500" /> Hot Topic
                    </div>
                    <a href={stock.news_url} target="_blank" className="text-sm text-slate-300 font-medium hover:text-indigo-400 line-clamp-1 transition-colors block">
                        {stock.news_title}
                    </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 4. 한국 시장 섹션 */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
             <div className="w-1 h-6 bg-red-500 rounded-full"></div>
             <h2 className="text-xl font-black italic tracking-tighter uppercase text-slate-100">Korea</h2>
          </div>
          <div className="flex flex-col gap-4">
            {krStocks.map((stock) => (
              <div key={stock.symbol} className="bg-slate-900 p-5 rounded-xl border border-slate-800 hover:border-red-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    {/* ⭐️ 이름(큰글씨) + 티커(작은글씨) 구조 */}
                    <div className="text-lg font-bold text-red-100 leading-tight">
                        {stock.company_name || stock.symbol}
                    </div>
                    <div className="text-xs font-bold text-slate-500 mt-1">{stock.symbol}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-lg text-white">{stock.price.toLocaleString()}</div>
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-950 ${getChangeColor(stock.change_percent)}`}>
                      {stock.change_percent > 0 ? "+" : ""}{stock.change_percent}%
                    </span>
                  </div>
                </div>

                {/* 뉴스 영역 */}
                <div className="relative pl-3 border-l-2 border-slate-700 hover:border-red-500 transition-colors">
                    <div className="text-[9px] text-slate-500 font-bold uppercase mb-1 flex items-center gap-1">
                        <Zap size={10} className="text-yellow-500" /> Hot Topic
                    </div>
                    <a href={stock.news_url} target="_blank" className="text-sm text-slate-300 font-medium hover:text-red-400 line-clamp-1 transition-colors block">
                        {stock.news_title}
                    </a>
                </div>
              </div>
            ))}
          </div>
        </section>

      </div>
    </main>
  );
}