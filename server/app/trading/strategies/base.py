from abc import ABC, abstractmethod

import pandas as pd


class TradingStrategy(ABC):
    """Abstract base class for all trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for the strategy."""
        ...

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the strategy to a DataFrame and return it with a 'signal' column.

        The input DataFrame must contain at least a 'close' column.
        The returned DataFrame will have an additional 'signal' column whose values
        are ``"buy"``, ``"sell"``, or ``None``.
        """
        ...
