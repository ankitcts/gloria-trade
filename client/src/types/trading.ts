export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit" | "stop" | "stop_limit";
export type OrderStatus =
  | "pending"
  | "submitted"
  | "partial"
  | "filled"
  | "cancelled"
  | "rejected";

export interface Order {
  id: string;
  user_id: string;
  security_id: string;
  side: OrderSide;
  order_type: OrderType;
  status: OrderStatus;
  quantity: number;
  price?: number;
  stop_price?: number;
  filled_quantity: number;
  filled_price?: number;
  created_at: string;
  updated_at: string;
}

export interface Trade {
  id: string;
  order_id: string;
  security_id: string;
  side: OrderSide;
  quantity: number;
  price: number;
  commission: number;
  executed_at: string;
}

export interface CreateOrderRequest {
  security_id: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  price?: number;
  stop_price?: number;
}
