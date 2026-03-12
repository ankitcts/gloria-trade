export interface Holding {
  id: string;
  security_id: string;
  security_symbol: string;
  security_name: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  cash_balance: number;
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_percent: number;
  holdings: Holding[];
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  portfolio_id: string;
  type: "deposit" | "withdrawal" | "buy" | "sell" | "dividend" | "fee";
  amount: number;
  security_id?: string;
  quantity?: number;
  price?: number;
  description?: string;
  created_at: string;
}
