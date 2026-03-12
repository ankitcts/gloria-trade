import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
import pandas as pd
import yfinance as yf

from app.models.security import Fundamentals, QuoteSnapshot

logger = logging.getLogger(__name__)

# Mapping from internal exchange codes to yfinance suffixes
_YFINANCE_SUFFIX_MAP: dict[str, str] = {
    "BSE": ".BO",
    "NSE": ".NS",
    "NASDAQ": "",
    "NYSE": "",
    "AMEX": "",
    "LSE": ".L",
    "TSE": ".T",
    "HKEX": ".HK",
    "SSE": ".SS",
    "SZSE": ".SZ",
    "ASX": ".AX",
    "TSX": ".TO",
    "XETRA": ".DE",
    "EURONEXT": ".PA",
}


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        exchange_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data and return as a DataFrame."""
        ...

    @abstractmethod
    async def get_quote(self, symbol: str, exchange_code: str) -> QuoteSnapshot:
        """Fetch a real-time (or delayed) quote snapshot."""
        ...

    @abstractmethod
    async def get_fundamentals(self, symbol: str, exchange_code: str) -> Fundamentals:
        """Fetch fundamental data for a security."""
        ...


class YFinanceProvider(DataProvider):
    """yfinance-backed market data provider."""

    # ── Symbol mapping ────────────────────────────────────────────────────

    @staticmethod
    def _map_symbol(symbol: str, exchange_code: str) -> str:
        """Convert an internal symbol + exchange code to a yfinance-compatible ticker.

        Examples:
            BSE:  "BOM500112"  -> strip "BOM" prefix -> "500112.BO"
            NSE:  "SBIN"       -> "SBIN.NS"
            NASDAQ/NYSE/AMEX:  "AAPL" -> "AAPL" (no suffix)
        """
        exchange_upper = exchange_code.upper()
        suffix = _YFINANCE_SUFFIX_MAP.get(exchange_upper, "")

        # BSE codes often come in as "BOM<numeric_code>" from the seed data
        if exchange_upper == "BSE" and symbol.upper().startswith("BOM"):
            symbol = symbol[3:]  # strip the "BOM" prefix

        return f"{symbol}{suffix}"

    # ── Historical data ───────────────────────────────────────────────────

    async def get_historical_data(
        self,
        symbol: str,
        exchange_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        yf_symbol = self._map_symbol(symbol, exchange_code)
        logger.info("Fetching historical data for %s (%s -> %s)", yf_symbol, start_date, end_date)

        loop = asyncio.get_event_loop()
        try:
            df = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    yf_symbol,
                    start=start_date.isoformat(),
                    end=(end_date + timedelta(days=1)).isoformat(),
                    auto_adjust=False,
                    progress=False,
                ),
            )
        except Exception as exc:
            logger.error("yfinance download error for %s: %s", yf_symbol, exc)
            return pd.DataFrame()

        if df is None or df.empty:
            logger.warning("No historical data returned for %s", yf_symbol)
            return pd.DataFrame()

        # Flatten multi-level columns if yfinance returns them
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Standardize column names
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Adj Close": "adj_close",
            }
        )

        # Ensure the index is a proper date column
        if df.index.name in ("Date", "date", None):
            df.index.name = "date"

        return df

    # ── Quote snapshot ────────────────────────────────────────────────────

    async def get_quote(self, symbol: str, exchange_code: str) -> QuoteSnapshot:
        yf_symbol = self._map_symbol(symbol, exchange_code)
        logger.info("Fetching quote for %s", yf_symbol)

        loop = asyncio.get_event_loop()
        try:
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
            info = await loop.run_in_executor(None, lambda: ticker.info)
        except Exception as exc:
            logger.error("yfinance quote error for %s: %s", yf_symbol, exc)
            return QuoteSnapshot()

        if not info:
            return QuoteSnapshot()

        return QuoteSnapshot(
            last_price=info.get("currentPrice") or info.get("regularMarketPrice"),
            change=info.get("regularMarketChange"),
            change_pct=info.get("regularMarketChangePercent"),
            open=info.get("regularMarketOpen") or info.get("open"),
            high=info.get("regularMarketDayHigh") or info.get("dayHigh"),
            low=info.get("regularMarketDayLow") or info.get("dayLow"),
            close=info.get("previousClose"),
            prev_close=info.get("regularMarketPreviousClose") or info.get("previousClose"),
            volume=info.get("regularMarketVolume") or info.get("volume"),
            bid=info.get("bid"),
            ask=info.get("ask"),
            timestamp=datetime.utcnow(),
        )

    # ── Fundamentals ──────────────────────────────────────────────────────

    async def get_fundamentals(self, symbol: str, exchange_code: str) -> Fundamentals:
        yf_symbol = self._map_symbol(symbol, exchange_code)
        logger.info("Fetching fundamentals for %s", yf_symbol)

        loop = asyncio.get_event_loop()
        try:
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
            info = await loop.run_in_executor(None, lambda: ticker.info)
        except Exception as exc:
            logger.error("yfinance fundamentals error for %s: %s", yf_symbol, exc)
            return Fundamentals()

        if not info:
            return Fundamentals()

        return Fundamentals(
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            pb_ratio=info.get("priceToBook"),
            eps=info.get("trailingEps"),
            dividend_yield_pct=(info.get("dividendYield") or 0) * 100 if info.get("dividendYield") else None,
            book_value=info.get("bookValue"),
            face_value=info.get("faceValue"),
            week_52_high=info.get("fiftyTwoWeekHigh"),
            week_52_low=info.get("fiftyTwoWeekLow"),
            avg_volume_30d=info.get("averageVolume"),
            beta=info.get("beta"),
            debt_to_equity=info.get("debtToEquity"),
            roe_pct=info.get("returnOnEquity"),
            updated_at=datetime.utcnow(),
        )


# Singleton provider instance
yfinance_provider = YFinanceProvider()
