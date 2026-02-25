"use client";

import { useEffect, useState } from "react";
import { db, auth, googleProvider, signInWithPopup, signOut } from "@/lib/firebase";
import { ref, onValue } from "firebase/database";
import { onAuthStateChanged, User } from "firebase/auth";
import {
  Activity, Zap, Globe, Briefcase, Star, ArrowUpRight
} from "lucide-react";
import AdBanner from "@/components/AdBanner";

interface MarketValue {
  price: number;
  change_percent: number;
  updated_at?: string;
}

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  volume?: number;
  sector?: string;
}

interface NewsItem {
  title: string;
  link: string;
  name: string;
  pubDate?: string;
}

interface FeedData {
  market_indices: {
    domestic?: Record<string, MarketValue>;
    global?: Record<string, MarketValue>;
  };
  key_indicators: Record<string, MarketValue>;
  stock_data: Record<string, StockData>;
  ai_summaries: { macro?: string; portfolio?: string; watchlist?: string };
  portfolio_list: string[];
  watchlist_list: string[];
  news_feed: { portfolio: NewsItem[]; watchlist: NewsItem[]; macro: NewsItem[] };
  updated_at: string;
}

export default function Dashboard() {
  const [data, setData] = useState<FeedData | null>(null);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'news'>('portfolio');
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const feedRef = ref(db, "/feed");
    const unsubscribe = onValue(feedRef, (snapshot) => {
      if (snapshot.exists()) setData(snapshot.val());
    });
    const unsubAuth = onAuthStateChanged(auth, setUser);
    return () => {
      unsubscribe();
      unsubAuth();
    };
  }, []);

  if (!data) return (
    <div className="flex h-screen items-center justify-center bg-slate-950 text-blue-500">
      <Activity className="animate-spin" size={48} />
    </div>
  );

  // ==================================================================
  // [구조 일치] 백엔드와 1:1 매칭되는 데이터 구조 정의
  // ==================================================================
  const market_indices = data.market_indices || {};
  const key_indicators = data.key_indicators || {};
  const stock_data = data.stock_data || {};
  const ai_summaries = data.ai_summaries || {};
  const portfolio_list = data.portfolio_list || [];
  const watchlist_list = data.watchlist_list || [];
  const news_feed = data.news_feed || { portfolio: [], watchlist: [], macro: [] };

  // 지표 리스트 준비
  const macroList = Object.entries(key_indicators);
  const indexList = [
    ...Object.entries(market_indices.domestic || {}),
    ...Object.entries(market_indices.global || {})
  ];

  // 종목 상세 정보 매핑
  const mapStockDetails = (list: string[]): StockData[] => list.map(symbol => {
    const safeKey = symbol.replace(".", "_");
    return stock_data[safeKey] || { symbol, name: symbol, price: 0, change_percent: 0 };
  });

  const myPortfolioStocks = mapStockDetails(portfolio_list);
  const watchListStocks = mapStockDetails(watchlist_list);
  const allNews = [...(news_feed.portfolio || []), ...(news_feed.watchlist || [])];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      
      {/* 1. 상단 광고 배너 */}
      <div className="bg-slate-950 py-4 flex justify-center border-b border-slate-900">
        <AdBanner type="top-banner" />
      </div>

      {/* 2. 2단 지표 바 (Sticky) */}
      <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-md border-b border-slate-800 shadow-xl">
        {/* 1층: MACRO 지표 */}
        <div className="border-b border-slate-800/50">
          <div className="max-w-7xl mx-auto px-4 h-12 flex items-center gap-6 overflow-x-auto no-scrollbar">
            <div className="flex-shrink-0 flex items-center gap-2 text-indigo-400 font-black text-[11px] border-r border-slate-800 pr-4 uppercase tracking-widest">
              <Globe size={14} /> Macro
            </div>
            <div className="flex items-center gap-8">
              {macroList.map(([name, val]: [string, MarketValue]) => (
                <div key={name} className="flex-shrink-0 flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">{name}</span>
                  <span className="font-mono text-sm font-bold text-white">{val.price?.toLocaleString() || val.price}</span>
                  <span className={`text-[10px] font-bold ${val.change_percent > 0 ? "text-red-400" : "text-blue-400"}`}>
                    {val.change_percent > 0 ? "▲" : "▼"}{Math.abs(val.change_percent)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 2층: MARKET 지수 + 로그인 버튼 */}
        <div>
          <div className="max-w-7xl mx-auto px-4 h-10 flex items-center gap-6 overflow-x-auto no-scrollbar">
            <div className="flex-shrink-0 flex items-center gap-2 text-slate-500 font-black text-[11px] border-r border-slate-800 pr-4 uppercase tracking-widest">
              <Activity size={14} /> Market
            </div>
            <div className="flex items-center gap-6">
              {indexList.map(([name, val]: [string, MarketValue]) => (
                <div key={name} className="flex-shrink-0 flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">{name}</span>
                  <span className="font-mono text-sm font-bold text-slate-300">{val.price?.toLocaleString()}</span>
                  <span className={`text-[10px] ${val.change_percent > 0 ? "text-red-400" : "text-blue-400"}`}>
                    ({val.change_percent > 0 ? "+" : ""}{val.change_percent}%)
                  </span>
                </div>
              ))}
            </div>
            {/* 로그인/로그아웃 버튼 */}
            <div className="ml-auto flex-shrink-0 pl-4">
              {user ? (
                <button
                  onClick={() => signOut(auth)}
                  className="flex items-center gap-2 text-[11px] text-slate-400 hover:text-white transition-colors"
                >
                  {user.photoURL && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={user.photoURL} className="w-6 h-6 rounded-full" alt="avatar" />
                  )}
                  <span className="hidden sm:inline">{user.displayName}</span>
                  <span className="text-slate-700">|</span>
                  <span>로그아웃</span>
                </button>
              ) : (
                <button
                  onClick={() => signInWithPopup(auth, googleProvider)}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold rounded-full transition-colors"
                >
                  Google 로그인
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 3. 본문 레이아웃 (광고-컨텐츠-광고) */}
      <div className="flex justify-center gap-8 px-4 mt-8">
        
        {/* 왼쪽 사이드 광고 */}
        <aside className="hidden 2xl:block w-[160px] flex-shrink-0">
          <div className="sticky top-32"><AdBanner type="side-banner" /></div>
        </aside>

        {/* 본문 영역 */}
        <div className="w-full max-w-7xl flex flex-col md:flex-row gap-8 pb-32">
          
          {/* LEFT: Portfolio & Watchlist */}
          <section className="md:w-[40%] space-y-6">
            <div className="bg-slate-900 rounded-3xl p-8 border border-slate-800 shadow-2xl">
              <h2 className="text-xl font-black italic text-blue-400 mb-8 flex items-center gap-2 uppercase tracking-tighter">
                <Briefcase size={20} /> My Portfolio
              </h2>
              <div className="border-b border-slate-800 pb-6 mb-6">
                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Balance</p>
                <p className="text-4xl font-black text-white tracking-tighter">₩ 142,500,000</p>
              </div>
              <div className="space-y-4">
                {myPortfolioStocks.map((stock) => (
                  <div key={stock.symbol} className="flex justify-between items-center group cursor-pointer">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-400 group-hover:border-blue-500 transition-colors">
                        {stock.symbol[0]}
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-200">{stock.name}</div>
                        <div className="text-[10px] text-slate-500 font-mono tracking-tight">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-mono font-bold text-slate-300">{stock.price?.toLocaleString()}</div>
                      <div className={`text-[10px] font-black ${stock.change_percent > 0 ? "text-red-400" : "text-blue-400"}`}>{stock.change_percent}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 rounded-3xl p-8 border border-slate-800">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6 flex items-center gap-2">
                <Star size={14} className="text-emerald-500 fill-emerald-500" /> Watchlist
              </h3>
              <div className="space-y-3">
                {watchListStocks.map((stock) => (
                  <div key={stock.symbol} className="flex justify-between items-center p-4 bg-slate-950/50 rounded-2xl border border-slate-800/50 hover:border-slate-600 transition-all">
                    <span className="font-bold text-slate-200 text-sm">{stock.name}</span>
                    <span className="font-mono text-sm font-bold text-slate-300">{stock.price?.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* RIGHT: AI Insight & News */}
          <section className="md:w-[60%] space-y-6">
            <div className="bg-gradient-to-br from-indigo-900/40 to-slate-950 p-8 rounded-3xl border border-indigo-500/20 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-10"><Zap size={100} className="text-indigo-400" /></div>
              <h2 className="text-indigo-400 font-black italic text-xl mb-6 flex items-center gap-2 uppercase tracking-tighter relative z-10">
                <Zap size={22} className="fill-indigo-400" /> Global Macro Insight
              </h2>
              <div className="text-slate-300 text-sm leading-8 whitespace-pre-wrap font-medium relative z-10">
                {ai_summaries.macro || "브리핑을 생성하는 중입니다..."}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900 p-6 rounded-3xl border border-slate-800">
                <h3 className="text-blue-400 font-bold text-[10px] uppercase tracking-widest mb-4 flex items-center gap-2"><Briefcase size={14} /> Asset Analysis</h3>
                <div className="text-slate-400 text-xs leading-6">{ai_summaries.portfolio || "분석 대기"}</div>
              </div>
              <div className="bg-slate-900 p-6 rounded-3xl border border-slate-800">
                <h3 className="text-emerald-400 font-bold text-[10px] uppercase tracking-widest mb-4 flex items-center gap-2"><Star size={14} /> Watchlist Trends</h3>
                <div className="text-slate-400 text-xs leading-6">{ai_summaries.watchlist || "분석 대기"}</div>
              </div>
            </div>

            <AdBanner type="in-feed" />

            <div className="space-y-4 pt-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Latest Market Headlines</h3>
              {allNews.map((news, idx) => (
                <div key={`${news.link}-${idx}`} className="group bg-slate-900 p-5 rounded-2xl border border-slate-800 hover:border-slate-600 transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex-1 pr-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-0.5 bg-slate-800 rounded text-[9px] text-slate-500 font-black uppercase tracking-widest">{news.name}</span>
                      </div>
                      <a href={news.link} target="_blank" className="text-sm font-bold text-slate-200 group-hover:text-blue-400 transition-colors leading-relaxed block">
                        {news.title}
                      </a>
                    </div>
                    <ArrowUpRight size={20} className="text-slate-700 group-hover:text-white transition-colors shrink-0 mt-1" />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* 오른쪽 사이드 광고 */}
        <aside className="hidden 2xl:block w-[160px] flex-shrink-0">
          <div className="sticky top-32"><AdBanner type="side-banner" /></div>
        </aside>
      </div>
    </main>
  );
}