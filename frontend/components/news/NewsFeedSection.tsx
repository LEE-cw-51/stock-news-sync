"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Globe, Briefcase, Star } from "lucide-react";
import type { ReactNode } from "react";
import AISummaryCard from "./AISummaryCard";
import NewsCard from "./NewsCard";
import AdBanner from "@/components/AdBanner";
import type { NewsItem, AISummaryStructured, WatchlistItem } from "@/lib/types";

type TabType = "macro" | "portfolio" | "watchlist";

interface Tab {
  id: TabType;
  label: string;
  icon: ReactNode;
}

const TABS: Tab[] = [
  { id: "macro", label: "거시경제", icon: <Globe size={13} /> },
  { id: "portfolio", label: "포트폴리오", icon: <Briefcase size={13} /> },
  { id: "watchlist", label: "관심종목", icon: <Star size={13} /> },
];

const CLICK_HISTORY_KEY = "stock_news_click_history";
const MAX_CLICK_HISTORY = 50;

interface ClientState {
  mounted: boolean;
  clickHistory: Record<string, number>;
}

interface NewsFeedSectionProps {
  newsFeed?: {
    macro?: NewsItem[];
    portfolio?: NewsItem[];
    watchlist?: NewsItem[];
  };
  aiSummaries?: {
    macro?: string | AISummaryStructured;
    portfolio?: string | AISummaryStructured;
    watchlist?: string | AISummaryStructured;
  };
  userWatchlist?: WatchlistItem[];
}

export default function NewsFeedSection({
  newsFeed,
  aiSummaries,
  userWatchlist,
}: NewsFeedSectionProps) {
  const [activeTab, setActiveTab] = useState<TabType>("macro");
  // Hydration 에러 방지: 단일 setState로 mounted + clickHistory를 동시에 설정
  const [clientState, setClientState] = useState<ClientState>({
    mounted: false,
    clickHistory: {},
  });

  useEffect(() => {
    let clickHistory: Record<string, number> = {};
    try {
      const stored = localStorage.getItem(CLICK_HISTORY_KEY);
      if (stored) clickHistory = JSON.parse(stored) as Record<string, number>;
    } catch {
      // localStorage 비활성화 또는 파싱 실패 — 무시
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setClientState({ mounted: true, clickHistory }); // SSR 하이드레이션 안전: 마운트 후 1회만 실행
  }, []);

  const handleNewsClick = useCallback((symbol: string) => {
    setClientState((prev) => {
      const next = { ...prev.clickHistory, [symbol]: (prev.clickHistory[symbol] ?? 0) + 1 };
      // 최대 50개 유지: 클릭 횟수 내림차순 정렬 후 자르기
      const pruned = Object.fromEntries(
        Object.entries(next)
          .sort((a, b) => b[1] - a[1])
          .slice(0, MAX_CLICK_HISTORY)
      );
      try {
        localStorage.setItem(CLICK_HISTORY_KEY, JSON.stringify(pruned));
      } catch {
        // 저장 실패 — 무시
      }
      return { ...prev, clickHistory: pruned };
    });
  }, []);

  const summary = aiSummaries?.[activeTab];

  const watchlistSymbols = useMemo(
    () => new Set(userWatchlist?.map((w) => w.symbol) ?? []),
    [userWatchlist]
  );

  // isMounted + 비매크로 탭일 때만 정렬 적용 (SSR 결과와 일치 보장)
  const sortedNewsList = useMemo(() => {
    const rawList = newsFeed?.[activeTab] ?? [];
    if (!clientState.mounted || activeTab === "macro" || !userWatchlist?.length) {
      return rawList;
    }
    return [...rawList].sort((a, b) => {
      const aIn = a.symbol && watchlistSymbols.has(a.symbol) ? 1 : 0;
      const bIn = b.symbol && watchlistSymbols.has(b.symbol) ? 1 : 0;
      if (bIn !== aIn) return bIn - aIn;
      // 관심 종목 내에서 클릭 횟수 많을수록 상단
      if (aIn && bIn) {
        const aClicks = (a.symbol && clientState.clickHistory[a.symbol]) ?? 0;
        const bClicks = (b.symbol && clientState.clickHistory[b.symbol]) ?? 0;
        if (bClicks !== aClicks) return bClicks - aClicks;
      }
      return 0;
    });
  }, [clientState, newsFeed, activeTab, userWatchlist, watchlistSymbols]);

  return (
    <section className="space-y-6">
      {/* 탭 네비게이션 */}
      <div className="flex gap-1 bg-slate-900 p-1 rounded-2xl border border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white shadow-lg shadow-blue-900/30"
                : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* AI 요약 카드 */}
      <AISummaryCard category={activeTab} summary={summary} />

      {/* 인피드 광고 */}
      <AdBanner type="in-feed" />

      {/* 뉴스 목록 */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          Latest Headlines
        </h3>
        {sortedNewsList.length > 0 ? (
          sortedNewsList.map((news, idx) => (
            <NewsCard
              key={`${news.link}-${idx}`}
              news={news}
              onNewsClick={handleNewsClick}
            />
          ))
        ) : (
          <div className="text-center py-12 text-slate-600 text-sm">
            최신 뉴스가 없습니다.
          </div>
        )}
      </div>
    </section>
  );
}
