import type { MarketValue } from "@/lib/types";

interface MarketIndexCardProps {
  name: string;
  value: MarketValue;
  variant?: "macro" | "index";
}

export default function MarketIndexCard({
  name,
  value,
  variant = "index",
}: MarketIndexCardProps) {
  const isPositive = value.change_percent > 0;
  const changeColor = isPositive ? "text-red-400" : "text-blue-400";

  if (variant === "macro") {
    return (
      <div className="flex-shrink-0 flex items-center gap-2">
        <span className="text-[10px] text-slate-500 font-bold uppercase">{name}</span>
        <span className="font-mono text-sm font-bold text-white">
          {value.price?.toLocaleString()}
        </span>
        <span className={`text-[10px] font-bold ${changeColor}`}>
          {isPositive ? "▲" : "▼"}
          {Math.abs(value.change_percent)}%
        </span>
      </div>
    );
  }

  return (
    <div className="flex-shrink-0 flex items-center gap-2">
      <span className="text-[10px] text-slate-500 font-bold uppercase">{name}</span>
      <span className="font-mono text-sm font-bold text-slate-300">
        {value.price?.toLocaleString()}
      </span>
      <span className={`text-[10px] ${changeColor}`}>
        ({isPositive ? "+" : ""}
        {value.change_percent}%)
      </span>
    </div>
  );
}
