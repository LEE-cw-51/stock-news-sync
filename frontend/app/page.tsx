"use client";

import { useCallback, useEffect, useState } from "react";
import { supabase, onAuthStateChange } from "@/lib/supabase";
import type { User } from "@/lib/supabase";
import { Activity, Briefcase, Star } from "lucide-react";
import AdBanner from "@/components/AdBanner";
import Header from "@/components/layout/Header";
import StockRow from "@/components/portfolio/StockRow";
import NewsFeedSection from "@/components/news/NewsFeedSection";
import type { FeedData, MarketValue, StockData, WatchlistItem } from "@/lib/types";

export default function Dashboard() {
  const [data, setData] = useState<FeedData | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [userWatchlist, setUserWatchlist] = useState<WatchlistItem[]>([]);

  // 개인 Watchlist 로드 (Supabase RPC)
  const loadUserWatchlist = useCallback(async (uid: string) => {
    const { data: rows, error } = await supabase.rpc("get_user_watchlist", {
      p_user_id: uid,
    });
    if (error) {
      console.error("watchlist 로드 오류:", error.message);
      return;
    }
    setUserWatchlist((rows as WatchlistItem[]) ?? []);
  }, []);

  useEffect(() => {
    // Supabase에서 최초 데이터 로드
    const loadInitialData = async () => {
      const { data: rows, error } = await supabase
        .from("feed")
        .select("*")
        .eq("id", 1)
        .single();
      if (!error && rows) {
        setData(rows as FeedData);
      }
    };
    loadInitialData();

    // Supabase Realtime 구독
    const channel = supabase
      .channel("feed-changes")
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "feed", filter: "id=eq.1" },
        (payload) => {
          setData(payload.new as FeedData);
        }
      )
      .subscribe();

    // Auth 구독
    const unsubAuth = onAuthStateChange((u) => {
      setUser(u);
      if (u) {
        loadUserWatchlist(u.id);
      } else {
        setUserWatchlist([]);
      }
    });

    return () => {
      supabase.removeChannel(channel);
      unsubAuth();
    };
  }, [loadUserWatchlist]);

  // 관심종목 추가
  const handleAdd = useCallback(
    async (stock: StockData) => {
      if (!user) return;
      const { error } = await supabase.rpc("add_to_watchlist", {
        p_user_id: user.id,
        p_symbol: stock.symbol,
        p_name: stock.name,
        p_sector: stock.sector ?? null,
      });
      if (error) {
        console.error("watchlist 추가 오류:", error.message);
        return;
      }
      await loadUserWatchlist(user.id);
    },
    [user, loadUserWatchlist]
  );

  // 관심종목 제거
  const handleRemove = useCallback(
    async (symbol: string) => {
      if (!user) return;
      const { error } = await supabase.rpc("remove_from_watchlist", {
        p_user_id: user.id,
        p_symbol: symbol,
      });
      if (error) {
        console.error("watchlist 제거 오류:", error.message);
        return;
      }
      await loadUserWatchlist(user.id);
    },
    [user, loadUserWatchlist]
  );

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

  // 로그인 시: 개인 Supabase watchlist / 비로그인 시: Firebase 전체 watchlist
  const userWatchlistSymbols = new Set(userWatchlist.map((w) => w.symbol));
  const myWatchlistStocks: StockData[] = user
    ? userWatchlist.map((w) => {
        const safeKey = w.symbol.replace(".", "_");
        return (
          (stock_data[safeKey] as StockData) ?? {
            symbol: w.symbol,
            name: w.name,
            price: 0,
            change_percent: 0,
            sector: w.sector,
          }
        );
      })
    : mapStockDetails(watchlist_list);

  // 로그인 시: 아직 내 watchlist에 없는 Firebase 종목 = 추가 후보
  const suggestedStocks: StockData[] = user
    ? mapStockDetails(
        watchlist_list.filter((sym) => !userWatchlistSymbols.has(sym))
      )
    : [];

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
                <Star size={14} className="text-emerald-500 fill-emerald-500" />
                Watchlist
                {user && (
                  <span className="ml-auto text-[10px] text-slate-600 normal-case font-normal">
                    내 관심종목
                  </span>
                )}
              </h3>

              {/* 내 관심종목 */}
              <div className="space-y-3">
                {myWatchlistStocks.length === 0 && user ? (
                  <p className="text-slate-600 text-xs text-center py-4">
                    아래 후보 목록에서 + 버튼으로 추가하세요
                  </p>
                ) : (
                  myWatchlistStocks.map((stock) => (
                    <StockRow
                      key={stock.symbol}
                      stock={stock}
                      variant="watchlist"
                      onRemove={user ? () => handleRemove(stock.symbol) : undefined}
                    />
                  ))
                )}
              </div>

              {/* 추가 후보 (로그인 시, 아직 내 watchlist에 없는 종목) */}
              {user && suggestedStocks.length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-800">
                  <p className="text-[10px] text-slate-600 uppercase font-bold tracking-widest mb-3">
                    추가 가능 종목
                  </p>
                  <div className="space-y-2">
                    {suggestedStocks.map((stock) => (
                      <StockRow
                        key={stock.symbol}
                        stock={stock}
                        variant="watchlist"
                        onAdd={() => handleAdd(stock)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

          </section>

          {/* RIGHT: 뉴스 피드 (탭 네비게이션 + AI 요약 + 뉴스) */}
          <section className="w-full md:w-[60%]">
            <NewsFeedSection newsFeed={news_feed} aiSummaries={ai_summaries} userWatchlist={userWatchlist} />
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
