export interface StockHistory {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
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
    macro?: string;
    portfolio?: string;
    watchlist?: string;
  };
  portfolio_list?: string[];
  watchlist_list?: string[];
  news_feed?: {
    macro?: NewsItem[];
    portfolio?: NewsItem[];
    watchlist?: NewsItem[];
  };
}
