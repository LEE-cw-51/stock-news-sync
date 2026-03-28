"use client";

import { Zap, Briefcase, Star } from "lucide-react";
import type { ReactNode } from "react";
import type { AISummaryStructured, GlossaryTerm } from "@/lib/types";

interface ParsedSummary {
  bullets: string[];
  sentiment: "호재" | "악재" | "중립" | null;
  sentimentDesc: string;
  trendInsight: string;
  glossaryTerms: GlossaryTerm[];
  flowExplanation: string;
  keyEvent: string;
  expectedImpact: string;
  referenceIndicators: string[];
}

function parseAISummary(text: string): ParsedSummary {
  const lines = text.split("\n").filter(Boolean);
  const bullets: string[] = [];
  let sentiment: "호재" | "악재" | "중립" | null = null;
  let sentimentDesc = "";
  let trendInsight = "";
  let inTrend = false;

  for (const line of lines) {
    const cleaned = line.replace(/\*\*/g, "").trim();
    if (cleaned.startsWith("- ")) {
      bullets.push(cleaned.slice(2));
      inTrend = false;
      continue;
    }
    if (cleaned.includes("📈") && cleaned.includes("추세 인사이트")) {
      inTrend = true;
      const colonIdx = cleaned.indexOf(":");
      if (colonIdx !== -1) trendInsight = cleaned.slice(colonIdx + 1).trim();
      continue;
    }
    if (inTrend && cleaned && !cleaned.match(/^[1-9]\./)) {
      trendInsight += (trendInsight ? " " : "") + cleaned;
      continue;
    }
    inTrend = false;
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

  return {
    bullets, sentiment, sentimentDesc, trendInsight,
    glossaryTerms: [], flowExplanation: "",
    keyEvent: "", expectedImpact: "", referenceIndicators: [],
  };
}

function normalizeAISummary(input: string | AISummaryStructured): ParsedSummary {
  if (typeof input === "object" && input !== null) {
    // JSON 구조화 데이터 → 직접 매핑
    return {
      bullets: input.bullets ?? [],
      sentiment: (["호재", "악재", "중립"].includes(input.market_reaction?.verdict)
        ? input.market_reaction.verdict
        : null) as "호재" | "악재" | "중립" | null,
      sentimentDesc: input.market_reaction?.reason ?? "",
      trendInsight: input.trend_insight ?? "",
      glossaryTerms: input.glossary_terms ?? [],
      flowExplanation: input.flow_explanation ?? "",
      keyEvent: input.key_event ?? "",
      expectedImpact: input.expected_impact ?? "",
      referenceIndicators: input.reference_indicators ?? [],
    };
  }
  // 문자열 → 기존 정규식 파서 폴백 (하위 호환)
  return parseAISummary(input);
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
  summary?: string | AISummaryStructured;
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

  const parsed = normalizeAISummary(summary);
  const hasContent =
    parsed.bullets.length > 0 ||
    !!parsed.keyEvent ||
    !!parsed.expectedImpact ||
    parsed.referenceIndicators.length > 0 ||
    !!parsed.flowExplanation ||
    !!parsed.trendInsight;

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

      {hasContent ? (
        <div className="relative z-10">
          {/* 📌 핵심 사건 */}
          {parsed.keyEvent && (
            <div className="mb-4 pb-4 border-b border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">
                📌 핵심 사건
              </p>
              <p className="text-slate-300 text-[12px] leading-relaxed font-medium">
                {parsed.keyEvent}
              </p>
            </div>
          )}

          {/* 📊 예상 영향 */}
          {parsed.expectedImpact && (
            <div className="mb-4 pb-4 border-b border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">
                📊 예상 영향
              </p>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {parsed.expectedImpact}
              </p>
            </div>
          )}

          {/* 🔎 참고 지표 */}
          {parsed.referenceIndicators.length > 0 && (
            <div className="mb-4 pb-4 border-b border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">
                🔎 참고 지표
              </p>
              <div className="flex flex-wrap gap-1.5">
                {parsed.referenceIndicators.map((ind, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-slate-800 rounded-full text-[10px] text-slate-400 border border-slate-700"
                  >
                    {ind}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 🔍 핵심 요약 (보조 수치) */}
          {parsed.bullets.length > 0 && (
            <>
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
            </>
          )}

          {/* 🔗 시장 흐름 */}
          {parsed.flowExplanation && (
            <div className="mt-3 pt-3 border-t border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">
                🔗 시장 흐름
              </p>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {parsed.flowExplanation}
              </p>
            </div>
          )}

          {/* 📈 추세 인사이트 */}
          {parsed.trendInsight && parsed.trendInsight !== "추세 데이터 없음" && (
            <div className="mt-3 pt-3 border-t border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">
                📈 추세 인사이트
              </p>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {parsed.trendInsight}
              </p>
            </div>
          )}

          {/* 📖 용어 설명 */}
          {parsed.glossaryTerms.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-800/50">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">
                📖 용어 설명
              </p>
              <dl className="space-y-2">
                {parsed.glossaryTerms.map((item, idx) => (
                  <div key={idx}>
                    <dt className="text-slate-300 text-[11px] font-bold">{item.term}</dt>
                    <dd className="text-slate-400 text-[11px] leading-relaxed">{item.definition}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* 감정 배지 */}
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
          {typeof summary === "string" ? summary : ""}
        </div>
      )}
    </div>
  );
}
