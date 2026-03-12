export interface Security {
  id: string;
  symbol: string;
  name: string;
  security_type: string;
  sector?: string;
  industry?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PriceHistory {
  id: string;
  security_id: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close?: number;
}

export interface ExchangeListing {
  id: string;
  security_id: string;
  exchange: string;
  ticker: string;
  is_primary: boolean;
  listed_date?: string;
  delisted_date?: string;
}

export interface SecurityDetail extends Security {
  exchange_listings: ExchangeListing[];
  latest_price?: PriceHistory;
}
