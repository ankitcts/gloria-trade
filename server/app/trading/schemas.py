from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Historic signal schemas ---


class HistoricSignal(BaseModel):
    date: str
    close: float
    sma30: Optional[float] = None
    sma100: Optional[float] = None
    signal: Optional[str] = None  # "buy", "sell", or None


class HistoricSignalsResponse(BaseModel):
    security_id: str
    symbol: str
    signals: list[HistoricSignal]
    total_signals: int
    buy_count: int
    sell_count: int


# --- Simulation schemas ---


class SimulateRequest(BaseModel):
    profit_pct: float = Field(default=2.0, ge=0.01, le=50.0, description="Profit trigger percentage")
    loss_pct: float = Field(default=2.0, ge=0.01, le=50.0, description="Loss trigger percentage")
    ticks: int = Field(default=400, ge=50, le=5000, description="Number of simulated ticks")


class TradeRecord(BaseModel):
    action: str  # "buy" or "sell"
    price: float
    quantity: int
    timestamp: datetime
    profit: Optional[float] = None  # only for sells


class SimulationTick(BaseModel):
    index: int
    timestamp: datetime
    price: float
    sma30: Optional[float] = None
    sma100: Optional[float] = None
    signal: Optional[str] = None  # "buy", "sell", or None
    position: Optional[str] = None  # "long" or None


class SimulationResult(BaseModel):
    security_id: str
    symbol: str
    ticks: list[SimulationTick]
    trades: list[TradeRecord]
    total_profit: float
    total_trades: int
