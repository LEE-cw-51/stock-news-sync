export interface WatchlistItem {
  id: number;
  user_id: string;
  symbol: string;
  name: string;
  sector?: string;
}

export interface MarketValue {
  price: number;
  change_percent: number;
  updated_at?: string;
}

export interface StockData {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  volume?: number;
  sector?: string;
}

export interface NewsItem {
  title: string;
  link: string;
  name: string;
  pubDate?: string;
  symbol?: string | null;
}

export interface GlossaryTerm {
  term: string;
  definition: string;
}

export interface AISummaryStructured {
  bullets?: string[];
  market_reaction: {
    verdict: "호재" | "악재" | "중립";
    reason: string;
  };
  trend_insight?: string;
  glossary_terms?: GlossaryTerm[];
  flow_explanation?: string;
  key_event?: string;
  expected_impact?: string;
  reference_indicators?: string[];
}

export interface FeedData {
  updated_at?: string;
  market_indices?: {
    domestic?: Record<string, MarketValue>;
    global?: Record<string, MarketValue>;
  };
  key_indicators?: Record<string, MarketValue>;
  stock_data?: Record<string, StockData>;
  ai_summaries?: {
    macro?: string | AISummaryStructured;
    portfolio?: string | AISummaryStructured;
    watchlist?: string | AISummaryStructured;
  };
  portfolio_list?: string[];
  watchlist_list?: string[];
  news_feed?: {
    macro?: NewsItem[];
    portfolio?: NewsItem[];
    watchlist?: NewsItem[];
  };
}
