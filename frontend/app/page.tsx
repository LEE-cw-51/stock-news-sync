"use client";

import { useEffect, useState } from "react";
import { db, auth } from "@/lib/firebase";
import { ref, onValue } from "firebase/database";
import { onAuthStateChanged } from "firebase/auth";
import type { User } from "firebase/auth";
import { Activity, Briefcase, Star } from "lucide-react";
import AdBanner from "@/components/AdBanner";
import Header from "@/components/layout/Header";
import StockRow from "@/components/portfolio/StockRow";
import NewsFeedSection from "@/components/news/NewsFeedSection";
import type { FeedData, MarketValue, StockData } from "@/lib/types";

export default function Dashboard() {
  const [data, setData] = useState<FeedData | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const feedRef = ref(db, "/feed");
    const unsubscribe = onValue(feedRef, (snapshot) => {
      if (snapshot.exists()) setData(snapshot.val() as FeedData);
    });
    const unsubAuth = onAuthStateChanged(auth, setUser);
    return () => {
      unsubscribe();
      unsubAuth();
    };
  }, []);

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-blue-500">
        <Activity className="animate-spin" size={48} />
      </div>
    );
  }

  // 데이터 구조 분리 (백엔드 /feed/ 경로 1:1 매핑)
  const market_indices = data.market_indices ?? {};
  const key_indicators = data.key_indicators ?? {};
  const stock_data = data.stock_data ?? {};
  const ai_summaries = data.ai_summaries ?? {};
  const portfolio_list = data.portfolio_list ?? [];
  const watchlist_list = data.watchlist_list ?? [];
  const news_feed = data.news_feed ?? {};

  const macroList = Object.entries(key_indicators) as [string, MarketValue][];
  const indexList = [
    ...Object.entries(market_indices.domestic ?? {}),
    ...Object.entries(market_indices.global ?? {}),
  ] as [string, MarketValue][];

  const mapStockDetails = (list: string[]): StockData[] =>
    list.map((symbol) => {
      const safeKey = symbol.replace(".", "_");
      return (
        (stock_data[safeKey] as StockData) ?? {
          symbol,
          name: symbol,
          price: 0,
          change_percent: 0,
        }
      );
    });

  const myPortfolioStocks = mapStockDetails(portfolio_list);
  const watchListStocks = mapStockDetails(watchlist_list);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-200 font-sans">

      {/* 1. 상단 광고 배너 */}
      <div className="bg-slate-950 py-4 flex justify-center border-b border-slate-900">
        <AdBanner type="top-banner" />
      </div>

      {/* 2. 헤더 (지표 + 인덱스 + 인증) */}
      <Header macroList={macroList} indexList={indexList} user={user} />

      {/* 3. 본문 레이아웃 (사이드광고-컨텐츠-사이드광고) */}
      <div className="flex justify-center gap-8 px-4 mt-8">

        {/* 왼쪽 사이드 광고 */}
        <aside className="hidden 2xl:block w-[160px] flex-shrink-0" aria-label="광고 영역">
          <div className="sticky top-32">
            <AdBanner type="side-banner" />
          </div>
        </aside>

        {/* 본문 영역 */}
        <div className="w-full max-w-7xl flex flex-col md:flex-row gap-8 pb-32">

          {/* LEFT: 포트폴리오 & 관심종목 */}
          <section className="w-full md:w-[40%] space-y-6">

            {/* 포트폴리오 카드 */}
            <div className="bg-slate-900 rounded-3xl p-6 md:p-8 border border-slate-800 shadow-2xl">
              <h2 className="text-xl font-black italic text-blue-400 mb-8 flex items-center gap-2 uppercase tracking-tighter">
                <Briefcase size={20} /> My Portfolio
              </h2>
              <div className="border-b border-slate-800 pb-6 mb-6">
                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">
                  Total Balance
                </p>
                <p className="text-4xl font-black text-white tracking-tighter">
                  ₩ 142,500,000
                </p>
              </div>
              <div className="space-y-4">
                {myPortfolioStocks.map((stock) => (
                  <StockRow key={stock.symbol} stock={stock} variant="portfolio" />
                ))}
              </div>
            </div>

            {/* 관심종목 카드 */}
            <div className="bg-slate-900 rounded-3xl p-6 md:p-8 border border-slate-800">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6 flex items-center gap-2">
                <Star size={14} className="text-emerald-500 fill-emerald-500" /> Watchlist
              </h3>
              <div className="space-y-3">
                {watchListStocks.map((stock) => (
                  <StockRow key={stock.symbol} stock={stock} variant="watchlist" />
                ))}
              </div>
            </div>

          </section>

          {/* RIGHT: 뉴스 피드 (탭 네비게이션 + AI 요약 + 뉴스) */}
          <section className="w-full md:w-[60%]">
            <NewsFeedSection newsFeed={news_feed} aiSummaries={ai_summaries} />
          </section>

        </div>

        {/* 오른쪽 사이드 광고 */}
        <aside className="hidden 2xl:block w-[160px] flex-shrink-0" aria-label="광고 영역">
          <div className="sticky top-32">
            <AdBanner type="side-banner" />
          </div>
        </aside>

      </div>
    </main>
  );
}
