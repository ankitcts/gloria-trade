"""Trading simulation engine.

Generates synthetic intraday ticks using Gaussian noise (ported from
xt-ai-trading/server/create_data_set.py) and runs the SMA crossover +
profit/loss trigger strategy over them.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from app.models.price_history import PriceHistoryDaily
from app.models.security import Security
from app.trading.schemas import SimulationResult, SimulationTick, TradeRecord
from app.trading.strategies.sma_crossover import SMACrossoverStrategy


# ---------------------------------------------------------------------------
# Synthetic tick generation – ported from create_data_set.getDayRandomData()
# ---------------------------------------------------------------------------


def generate_intraday_ticks(
    base_price: float,
    num_ticks: int = 400,
    base_time: Optional[datetime] = None,
) -> list[dict]:
    """Generate *num_ticks* simulated intraday price ticks centred around
    *base_price* using a Gaussian distribution with a trend component.

    This is a faithful port of ``getDayRandomData()`` from the original
    ``create_data_set.py``.

    Returns a list of dicts with ``timestamp`` and ``price`` keys.
    """
    if base_time is None:
        today = datetime.utcnow().replace(hour=9, minute=15, second=0, microsecond=0)
        base_time = today

    mu = base_price
    sigma = 0.5
    percentage_val = mu * 0.5
    range_number = num_ticks

    prices: list[float] = []

    for index_1based in range(1, range_number + 1):
        # Piecewise trend delta – replicates original exactly
        first_25_pct = (percentage_val / range_number * 0.25)
        second_25_pct = (percentage_val / range_number * 0.25)
        third_30_pct = (percentage_val * 0.2 / range_number * 0.30)
        forth_20_pct = -(percentage_val / range_number * 0.20)

        if index_1based < range_number * 0.25:
            delta = first_25_pct * index_1based
        elif index_1based < range_number * 0.5:
            delta = second_25_pct * (index_1based / 2)
        elif index_1based < range_number * 0.8:
            delta = third_30_pct * (index_1based / 2)
        else:
            delta = forth_20_pct * index_1based

        price = random.normalvariate(mu + delta, sigma)
        prices.append(round(price, 2))

    # Build time axis – one tick per second starting from base_time
    ticks = []
    for i, price in enumerate(prices):
        ticks.append(
            {
                "timestamp": base_time + timedelta(seconds=i),
                "price": price,
            }
        )

    return ticks


# ---------------------------------------------------------------------------
# Full simulation runner
# ---------------------------------------------------------------------------


async def run_simulation(
    security_id: str,
    profit_pct: float = 2.0,
    loss_pct: float = 2.0,
    num_ticks: int = 400,
) -> SimulationResult:
    """Run a complete intraday trading simulation for a security.

    1. Fetch the security document to get symbol and latest close.
    2. Generate synthetic intraday ticks around the close price.
    3. Apply SMA crossover + profit/loss triggers.
    4. Collect trades and tally profit.
    """

    # --- Fetch security --------------------------------------------------
    security = await Security.get(security_id)
    if security is None:
        raise ValueError(f"Security {security_id} not found")

    # --- Determine base price (latest daily close) -----------------------
    latest_price_doc = await PriceHistoryDaily.find(
        PriceHistoryDaily.security_id == security_id,
    ).sort("-date").first_or_none()

    if latest_price_doc is not None:
        base_price = latest_price_doc.close
    elif security.quote and security.quote.last_price:
        base_price = security.quote.last_price
    else:
        # Reasonable fallback so the simulation is still runnable
        base_price = 100.0

    # --- Generate ticks --------------------------------------------------
    raw_ticks = generate_intraday_ticks(base_price, num_ticks)

    # Build a DataFrame with column names our strategy expects
    df = pd.DataFrame(raw_ticks)
    df["close"] = df["price"]

    # --- Apply strategy --------------------------------------------------
    strategy = SMACrossoverStrategy(
        short_window=30,
        long_window=100,
        profit_pct=profit_pct,
        loss_pct=loss_pct,
    )
    df = strategy.generate_signals(df)

    # --- Collect results -------------------------------------------------
    quantity = 100  # default lot size for simulation
    trades: list[TradeRecord] = []
    sim_ticks: list[SimulationTick] = []
    total_profit = 0.0
    current_buy_price: Optional[float] = None
    position: Optional[str] = None

    for i, row in df.iterrows():
        signal = row.get("signal")

        if signal == "buy":
            current_buy_price = row["price"]
            position = "long"
            trades.append(
                TradeRecord(
                    action="buy",
                    price=row["price"],
                    quantity=quantity,
                    timestamp=row["timestamp"],
                )
            )
        elif signal == "sell" and current_buy_price is not None:
            profit = (row["price"] - current_buy_price) * quantity
            total_profit += profit
            trades.append(
                TradeRecord(
                    action="sell",
                    price=row["price"],
                    quantity=quantity,
                    timestamp=row["timestamp"],
                    profit=round(profit, 2),
                )
            )
            current_buy_price = None
            position = None

        sim_ticks.append(
            SimulationTick(
                index=int(i),
                timestamp=row["timestamp"],
                price=row["price"],
                sma30=round(row["sma30"], 2) if pd.notna(row.get("sma30")) else None,
                sma100=round(row["sma100"], 2) if pd.notna(row.get("sma100")) else None,
                signal=signal,
                position=position,
            )
        )

    return SimulationResult(
        security_id=security_id,
        symbol=security.symbol,
        ticks=sim_ticks,
        trades=trades,
        total_profit=round(total_profit, 2),
        total_trades=len(trades),
    )
