"""Trading service – business logic layer.

Provides:
- Historic SMA crossover signal generation from daily price data.
- Simulation execution with order persistence.
- WebSocket connection management for streaming simulation ticks.
"""

import asyncio
from datetime import datetime
from typing import Optional

import pandas as pd
from beanie import PydanticObjectId
from fastapi import WebSocket

from app.models.order import Order, OrderSide, OrderStatus, OrderType, OrderValidity, FillRecord
from app.models.price_history import PriceHistoryDaily
from app.models.security import Security
from app.trading.schemas import (
    HistoricSignal,
    HistoricSignalsResponse,
    SimulationResult,
    TradeRecord,
)
from app.trading.simulation import run_simulation
from app.trading.strategies.sma_crossover import SMACrossoverStrategy


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages active WebSocket connections for trading simulations."""

    def __init__(self) -> None:
        self._active: dict[str, list[WebSocket]] = {}  # security_id -> connections

    async def connect(self, websocket: WebSocket, security_id: str) -> None:
        await websocket.accept()
        self._active.setdefault(security_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, security_id: str) -> None:
        conns = self._active.get(security_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._active.pop(security_id, None)

    async def send_json(self, websocket: WebSocket, data: dict) -> None:
        await websocket.send_json(data)

    async def broadcast(self, security_id: str, data: dict) -> None:
        for ws in self._active.get(security_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


# Singleton
ws_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Historic signals
# ---------------------------------------------------------------------------


async def get_historic_signals(security_id: str) -> HistoricSignalsResponse:
    """Apply SMA crossover to the full daily price history of a security
    and return every day annotated with its signal (if any).
    """

    security = await Security.get(security_id)
    if security is None:
        raise ValueError(f"Security {security_id} not found")

    # Fetch daily prices sorted ascending (oldest first)
    price_docs = await PriceHistoryDaily.find(
        PriceHistoryDaily.security_id == security_id,
    ).sort("+date").to_list()

    if not price_docs:
        return HistoricSignalsResponse(
            security_id=security_id,
            symbol=security.symbol,
            signals=[],
            total_signals=0,
            buy_count=0,
            sell_count=0,
        )

    # Build DataFrame
    rows = [{"date": str(p.date), "close": p.close} for p in price_docs]
    df = pd.DataFrame(rows)

    # Apply strategy (pure crossover – no profit/loss triggers)
    strategy = SMACrossoverStrategy(short_window=30, long_window=100)
    df = strategy.generate_signals(df)

    # Assemble response
    signals: list[HistoricSignal] = []
    buy_count = 0
    sell_count = 0

    for _, row in df.iterrows():
        sig = row.get("signal")
        if sig == "buy":
            buy_count += 1
        elif sig == "sell":
            sell_count += 1

        signals.append(
            HistoricSignal(
                date=row["date"],
                close=row["close"],
                sma30=round(row["sma30"], 2) if pd.notna(row.get("sma30")) else None,
                sma100=round(row["sma100"], 2) if pd.notna(row.get("sma100")) else None,
                signal=sig,
            )
        )

    return HistoricSignalsResponse(
        security_id=security_id,
        symbol=security.symbol,
        signals=signals,
        total_signals=buy_count + sell_count,
        buy_count=buy_count,
        sell_count=sell_count,
    )


# ---------------------------------------------------------------------------
# Run simulation + persist orders
# ---------------------------------------------------------------------------


async def run_trading_simulation(
    security_id: str,
    user_id: str,
    profit_pct: float = 2.0,
    loss_pct: float = 2.0,
    ticks: int = 400,
) -> SimulationResult:
    """Execute a simulation and persist each trade as an ``Order`` document
    with ``is_simulated=True``.
    """

    result = await run_simulation(
        security_id=security_id,
        profit_pct=profit_pct,
        loss_pct=loss_pct,
        num_ticks=ticks,
    )

    # Fetch security for order metadata
    security = await Security.get(security_id)

    # Persist each trade as an Order
    for trade in result.trades:
        order = Order(
            user_id=user_id,
            portfolio_id="simulation",
            security_id=security_id,
            symbol=security.symbol,
            exchange_code=security.primary_exchange_code,
            security_name=security.name,
            order_type=OrderType.MARKET,
            side=OrderSide.BUY if trade.action == "buy" else OrderSide.SELL,
            quantity=trade.quantity,
            filled_quantity=trade.quantity,
            avg_fill_price=trade.price,
            validity=OrderValidity.DAY,
            status=OrderStatus.FILLED,
            fills=[
                FillRecord(
                    fill_id=str(PydanticObjectId()),
                    quantity=trade.quantity,
                    price=trade.price,
                    filled_at=trade.timestamp,
                )
            ],
            total_amount=round(trade.price * trade.quantity, 2),
            currency=security.currency,
            realized_pnl=trade.profit,
            is_simulated=True,
            trigger_source="sma_crossover",
            trigger_details={
                "profit_pct": profit_pct,
                "loss_pct": loss_pct,
                "strategy": "sma_crossover",
            },
            placed_at=trade.timestamp,
            executed_at=trade.timestamp,
            notes=f"Auto-generated by SMA crossover simulation (profit={profit_pct}%, loss={loss_pct}%)",
        )
        await order.insert()

    return result


# ---------------------------------------------------------------------------
# WebSocket streaming simulation
# ---------------------------------------------------------------------------


async def stream_simulation(
    websocket: WebSocket,
    security_id: str,
    profit_pct: float = 2.0,
    loss_pct: float = 2.0,
    ticks: int = 400,
) -> None:
    """Stream a simulation tick-by-tick over a WebSocket connection.

    Each tick is sent as a JSON message with a 0.05 s delay for a
    real-time feel.
    """

    result = await run_simulation(
        security_id=security_id,
        profit_pct=profit_pct,
        loss_pct=loss_pct,
        num_ticks=ticks,
    )

    # Stream each tick
    for tick in result.ticks:
        await websocket.send_json(
            {
                "type": "tick",
                "data": tick.model_dump(mode="json"),
            }
        )
        await asyncio.sleep(0.05)

    # Send summary at the end
    await websocket.send_json(
        {
            "type": "summary",
            "data": {
                "security_id": result.security_id,
                "symbol": result.symbol,
                "total_profit": result.total_profit,
                "total_trades": result.total_trades,
                "trades": [t.model_dump(mode="json") for t in result.trades],
            },
        }
    )
