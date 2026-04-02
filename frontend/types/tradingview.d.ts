declare global {
  interface TradingViewWidgetOptions {
    autosize?: boolean;
    symbol: string;
    interval?: string;
    timezone?: string;
    theme?: "light" | "dark";
    style?: string;
    locale?: string;
    toolbar_bg?: string;
    enable_publishing?: boolean;
    hide_top_toolbar?: boolean;
    hide_side_toolbar?: boolean;
    withdateranges?: boolean;
    container_id: string;
  }

  interface TradingViewWidgetInstance {
    remove?: () => void;
  }

  interface TradingViewConstructor {
    new (options: TradingViewWidgetOptions): TradingViewWidgetInstance;
  }

  interface Window {
    TradingView?: { widget: TradingViewConstructor };
  }
}

export {};
