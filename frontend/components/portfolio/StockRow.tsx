import type { StockData } from "@/lib/types";

interface StockRowProps {
  stock: StockData;
  variant?: "portfolio" | "watchlist";
}

export default function StockRow({ stock, variant = "portfolio" }: StockRowProps) {
  const isPositive = stock.change_percent > 0;
  const changeColor = isPositive ? "text-red-400" : "text-blue-400";

  if (variant === "watchlist") {
    return (
      <div className="flex justify-between items-center p-4 bg-slate-950/50 rounded-2xl border border-slate-800/50 hover:border-slate-600 transition-all">
        <div>
          <span className="font-bold text-slate-200 text-sm">{stock.name}</span>
          {stock.sector && (
            <p className="text-[10px] text-slate-600 mt-0.5">{stock.sector}</p>
          )}
        </div>
        <div className="text-right">
          <div className="font-mono text-sm font-bold text-slate-300">
            {stock.price?.toLocaleString()}
          </div>
          <div className={`text-[10px] font-black ${changeColor}`}>
            {isPositive ? "+" : ""}
            {stock.change_percent}%
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-between items-center group cursor-pointer">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-400 group-hover:border-blue-500 transition-colors">
          {stock.symbol[0]}
        </div>
        <div>
          <div className="text-sm font-bold text-slate-200">{stock.name}</div>
          <div className="text-[10px] text-slate-500 font-mono tracking-tight">
            {stock.symbol}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm font-mono font-bold text-slate-300">
          {stock.price?.toLocaleString()}
        </div>
        <div className={`text-[10px] font-black ${changeColor}`}>
          {isPositive ? "+" : ""}
          {stock.change_percent}%
        </div>
      </div>
    </div>
  );
}
