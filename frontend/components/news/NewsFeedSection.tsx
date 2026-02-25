"use client";

import { useState } from "react";
import { Globe, Briefcase, Star } from "lucide-react";
import type { ReactNode } from "react";
import AISummaryCard from "./AISummaryCard";
import NewsCard from "./NewsCard";
import AdBanner from "@/components/AdBanner";
import type { NewsItem } from "@/lib/types";

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

interface NewsFeedSectionProps {
  newsFeed?: {
    macro?: NewsItem[];
    portfolio?: NewsItem[];
    watchlist?: NewsItem[];
  };
  aiSummaries?: {
    macro?: string;
    portfolio?: string;
    watchlist?: string;
  };
}

export default function NewsFeedSection({
  newsFeed,
  aiSummaries,
}: NewsFeedSectionProps) {
  const [activeTab, setActiveTab] = useState<TabType>("macro");

  const newsList = newsFeed?.[activeTab] ?? [];
  const summary = aiSummaries?.[activeTab];

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
        {newsList.length > 0 ? (
          newsList.map((news, idx) => (
            <NewsCard key={`${news.link}-${idx}`} news={news} />
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
