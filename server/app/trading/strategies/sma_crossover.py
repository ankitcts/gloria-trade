"""SMA Crossover Strategy – ported from xt-ai-trading/server/trade.py.

Two operating modes:

1. **Historic (SMA crossover only)** – used on daily price data.
   Buy when SMA30 crosses above SMA100; sell when SMA30 crosses below.

2. **Intraday simulation (profit / loss triggers)** – used on synthetic tick data.
   After a buy, sell when price rises by ``profit_pct`` % or falls by ``loss_pct`` %
   from the buy price.  If neither the SMA crossover nor the profit/loss trigger
   fires, no signal is emitted.
"""

from typing import Optional

import numpy as np
import pandas as pd

from app.trading.strategies.base import TradingStrategy


class SMACrossoverStrategy(TradingStrategy):
    """SMA-30 / SMA-100 crossover strategy with optional profit/loss triggers."""

    def __init__(
        self,
        short_window: int = 30,
        long_window: int = 100,
        profit_pct: Optional[float] = None,
        loss_pct: Optional[float] = None,
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.profit_pct = profit_pct
        self.loss_pct = loss_pct

    @property
    def name(self) -> str:
        return "SMA Crossover"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ``sma30``, ``sma100``, and ``signal`` columns to *df*.

        If ``profit_pct`` / ``loss_pct`` are set the intraday profit/loss
        trigger logic is applied *instead of* the pure crossover logic.
        """
        df = df.copy()

        df["sma30"] = df["close"].rolling(window=self.short_window, min_periods=1).mean()
        df["sma100"] = df["close"].rolling(window=self.long_window, min_periods=1).mean()

        if self.profit_pct is not None and self.loss_pct is not None:
            df["signal"] = self._apply_profit_loss_triggers(df)
        else:
            df["signal"] = self._apply_crossover_signals(df)

        return df

    # ------------------------------------------------------------------
    # Pure SMA crossover (historic mode) – ported from trade.buy_sell()
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_crossover_signals(df: pd.DataFrame) -> list:
        """Faithful port of the ``buy_sell()`` function from trade.py."""
        signals: list[Optional[str]] = []
        flag = -1

        for i in range(len(df)):
            sma30 = df["sma30"].iloc[i]
            sma100 = df["sma100"].iloc[i]

            if pd.isna(sma30) or pd.isna(sma100):
                signals.append(None)
                continue

            if sma30 > sma100:
                if flag != 1:
                    signals.append("buy")
                    flag = 1
                else:
                    signals.append(None)
            elif sma30 < sma100:
                if flag != 0:
                    signals.append("sell")
                    flag = 0
                else:
                    signals.append(None)
            else:
                signals.append(None)

        return signals

    # ------------------------------------------------------------------
    # Profit / loss trigger (intraday simulation) – ported from
    # trade.trigger_buy_sell() and trade.symbolDayData()
    # ------------------------------------------------------------------

    def _apply_profit_loss_triggers(self, df: pd.DataFrame) -> list:
        """Faithful port of ``trigger_buy_sell()`` combined with the
        iteration logic from ``symbolDayData()``."""
        signals: list[Optional[str]] = []
        is_bought = False
        is_sold = False
        buy_price = 0.0

        for i in range(len(df)):
            price = df["close"].iloc[i]
            result = self._trigger_buy_sell(
                price, is_bought, is_sold, self.profit_pct, self.loss_pct, buy_price,
            )

            signal = None
            if not np.isnan(result["buy"]):
                signal = "buy"
            elif not np.isnan(result["sell"]):
                signal = "sell"

            # State update – matches symbolDayData() logic exactly
            if is_bought:
                if result["is_sold"]:
                    is_bought = result["is_bought"]
                    is_sold = result["is_sold"]
            else:
                is_bought = result["is_bought"]
                is_sold = result["is_sold"]

            if result["is_bought"]:
                buy_price = price
            elif result["is_sold"]:
                buy_price = 0.0

            signals.append(signal)

        return signals

    @staticmethod
    def _trigger_buy_sell(
        price: float,
        is_bought: bool,
        is_sold: bool,
        profit_pct: float,
        loss_pct: float,
        buy_price: float,
    ) -> dict:
        """Faithful port of ``trigger_buy_sell()`` from trade.py."""
        sig_buy = np.nan
        sig_sell = np.nan
        sold = False
        bought = False

        if not is_bought and not is_sold:
            sig_buy = price
            sig_sell = np.nan
            bought = True
            sold = False
        else:
            if is_bought:
                if price >= buy_price + (buy_price * (profit_pct / 100)):
                    sold = True
                    bought = False
                    sig_buy = np.nan
                    sig_sell = price
                elif price <= buy_price - (buy_price * (loss_pct / 100)):
                    sold = True
                    bought = False
                    sig_buy = np.nan
                    sig_sell = price
                else:
                    sold = False
                    bought = False
                    sig_buy = np.nan
                    sig_sell = np.nan
            else:
                sig_buy = np.nan
                sig_sell = np.nan
                sold = False
                bought = False

        return {
            "buy": sig_buy,
            "sell": sig_sell,
            "is_bought": bought,
            "is_sold": sold,
        }
