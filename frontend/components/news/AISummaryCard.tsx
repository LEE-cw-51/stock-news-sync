import { Zap, Briefcase, Star } from "lucide-react";
import type { ReactNode } from "react";

interface ParsedSummary {
  bullets: string[];
  sentiment: "호재" | "악재" | "중립" | null;
  sentimentDesc: string;
}

function parseAISummary(text: string): ParsedSummary {
  const lines = text.split("\n").filter(Boolean);
  const bullets: string[] = [];
  let sentiment: "호재" | "악재" | "중립" | null = null;
  let sentimentDesc = "";

  for (const line of lines) {
    const cleaned = line.replace(/\*\*/g, "").trim();
    if (cleaned.startsWith("- ")) {
      bullets.push(cleaned.slice(2));
    }
    if (cleaned.includes("호재") && !sentiment) {
      sentiment = "호재";
      sentimentDesc = cleaned.replace(/📊[^:]*:\s*/, "");
    } else if (cleaned.includes("악재") && !sentiment) {
      sentiment = "악재";
      sentimentDesc = cleaned.replace(/📊[^:]*:\s*/, "");
    } else if (cleaned.includes("중립") && !sentiment) {
      sentiment = "중립";
      sentimentDesc = cleaned.replace(/📊[^:]*:\s*/, "");
    }
  }

  return { bullets, sentiment, sentimentDesc };
}

const SENTIMENT_STYLES = {
  호재: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  악재: "bg-red-500/20 text-red-400 border border-red-500/30",
  중립: "bg-slate-500/20 text-slate-400 border border-slate-500/30",
} as const;

type CategoryType = "macro" | "portfolio" | "watchlist";

interface CategoryStyle {
  icon: ReactNode;
  gradient: string;
  titleColor: string;
  title: string;
}

const CATEGORY_STYLES: Record<CategoryType, CategoryStyle> = {
  macro: {
    icon: <Zap size={20} className="fill-indigo-400 text-indigo-400" />,
    gradient: "bg-gradient-to-br from-indigo-900/40 to-slate-950 border-indigo-500/20",
    titleColor: "text-indigo-400",
    title: "Global Macro Insight",
  },
  portfolio: {
    icon: <Briefcase size={16} className="text-blue-400" />,
    gradient: "bg-slate-900/80 border-slate-800",
    titleColor: "text-blue-400",
    title: "Asset Analysis",
  },
  watchlist: {
    icon: <Star size={16} className="text-emerald-400" />,
    gradient: "bg-slate-900/80 border-slate-800",
    titleColor: "text-emerald-400",
    title: "Watchlist Trends",
  },
};

interface AISummaryCardProps {
  category: CategoryType;
  summary?: string;
}

export default function AISummaryCard({ category, summary }: AISummaryCardProps) {
  const style = CATEGORY_STYLES[category];

  if (!summary) {
    return (
      <div className={`p-6 rounded-3xl border ${style.gradient}`}>
        <h3
          className={`${style.titleColor} font-bold text-[10px] uppercase tracking-widest mb-3 flex items-center gap-2`}
        >
          {style.icon} {style.title}
        </h3>
        <p className="text-slate-600 text-xs">브리핑을 생성하는 중입니다...</p>
      </div>
    );
  }

  const parsed = parseAISummary(summary);

  return (
    <div className={`p-6 rounded-3xl border ${style.gradient} relative overflow-hidden`}>
      {category === "macro" && (
        <div className="absolute top-0 right-0 p-6 opacity-10 pointer-events-none">
          <Zap size={90} className="text-indigo-400" />
        </div>
      )}

      <h3
        className={`${style.titleColor} font-black italic text-base mb-4 flex items-center gap-2 uppercase tracking-tighter relative z-10`}
      >
        {style.icon} {style.title}
      </h3>

      {parsed.bullets.length > 0 ? (
        <div className="relative z-10">
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-3">
            🔍 핵심 요약
          </p>
          <ul className="space-y-2 mb-4">
            {parsed.bullets.map((bullet, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-slate-300 leading-relaxed"
              >
                <span className="text-slate-600 mt-1 flex-shrink-0">•</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>

          {parsed.sentiment && (
            <div className="mt-4 pt-4 border-t border-slate-800/50">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold ${SENTIMENT_STYLES[parsed.sentiment]}`}
              >
                {parsed.sentiment === "호재" ? "📈" : parsed.sentiment === "악재" ? "📉" : "➡️"}{" "}
                {parsed.sentiment}
              </span>
              {parsed.sentimentDesc && (
                <p className="text-slate-500 text-[11px] mt-2 leading-relaxed">
                  {parsed.sentimentDesc}
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="text-slate-300 text-sm leading-8 whitespace-pre-wrap font-medium relative z-10">
          {summary}
        </div>
      )}
    </div>
  );
}
