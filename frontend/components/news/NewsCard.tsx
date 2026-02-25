import { ArrowUpRight } from "lucide-react";
import type { NewsItem } from "@/lib/types";

function formatDate(pubDate?: string): string {
  if (!pubDate) return "";
  const date = new Date(pubDate);
  if (isNaN(date.getTime())) return "";
  const diff = Date.now() - date.getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return "방금 전";
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

interface NewsCardProps {
  news: NewsItem;
}

export default function NewsCard({ news }: NewsCardProps) {
  const dateStr = formatDate(news.pubDate);

  return (
    <div className="group bg-slate-900 p-5 rounded-2xl border border-slate-800 hover:border-slate-600 transition-all">
      <div className="flex justify-between items-start">
        <div className="flex-1 pr-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 bg-slate-800 rounded text-[9px] text-slate-500 font-black uppercase tracking-widest">
              {news.name}
            </span>
            {dateStr && (
              <span className="text-[9px] text-slate-600">{dateStr}</span>
            )}
          </div>
          <a
            href={news.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-bold text-slate-200 group-hover:text-blue-400 transition-colors leading-relaxed block"
          >
            {news.title}
          </a>
        </div>
        <ArrowUpRight
          size={20}
          className="text-slate-700 group-hover:text-white transition-colors shrink-0 mt-1"
        />
      </div>
    </div>
  );
}
