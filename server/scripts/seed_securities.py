#!/usr/bin/env python3
"""Seed securities into MongoDB from BSE CSV and NSE JSON data files.

Usage:
    cd server
    python -m scripts.seed_securities

Or directly:
    python scripts/seed_securities.py
"""

import asyncio
import csv
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# Ensure the server package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, close_db
from app.models.security import ExchangeListing, Security, SecurityType

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SEED_DIR = Path(__file__).resolve().parent / "seed_data"
BSE_CSV = SEED_DIR / "stocks_bse.csv"
NSE_JSON = SEED_DIR / "nse_stocks_list.json"


def _clean_name(raw: str) -> str:
    """Strip common suffixes like 'EOD Prices' and 'Adjusted Stock Prices'."""
    name = raw.strip()
    # Remove "EOD Prices" suffix (BSE)
    name = re.sub(r"\s+EOD\s+Prices$", "", name, flags=re.IGNORECASE)
    # Remove "(EQ...) Adjusted/Unadjusted Stock Prices" suffix (NSE)
    name = re.sub(r"\s*\(EQ[^)]*\)\s*(Un)?[Aa]djusted\s+Stock\s+Prices$", "", name)
    return name.strip()


def _bse_code_to_yfinance(bse_code: str) -> str:
    """Convert BSE code like 'BOM500112' to yfinance symbol '500112.BO'."""
    numeric = bse_code
    if bse_code.upper().startswith("BOM"):
        numeric = bse_code[3:]
    return f"{numeric}.BO"


async def seed_bse(dry_run: bool = False) -> int:
    """Read stocks_bse.csv and upsert Security documents.

    CSV columns: description, code, type
    Example row: "20 Microns Ltd. EOD Prices", "BOM533022", "BSE"
    """
    if not BSE_CSV.exists():
        logger.warning("BSE CSV not found at %s – skipping", BSE_CSV)
        return 0

    count = 0
    with open(BSE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = row.get("description", "").strip()
            bse_code = row.get("code", "").strip()
            sec_type = row.get("type", "BSE").strip()

            if not bse_code:
                continue

            name = _clean_name(raw_name)
            # The symbol is the BSE code (e.g. BOM533022)
            symbol = bse_code
            # Strip BOM prefix for the ticker used in the listing
            ticker = bse_code[3:] if bse_code.upper().startswith("BOM") else bse_code
            yf_symbol = _bse_code_to_yfinance(bse_code)

            # Check for existing security to avoid duplicates
            existing = await Security.find_one(
                Security.symbol == symbol,
                Security.primary_exchange_code == "BSE",
            )
            if existing:
                continue

            security = Security(
                symbol=symbol,
                name=name or symbol,
                security_type=SecurityType.EQUITY,
                listings=[
                    ExchangeListing(
                        exchange_code="BSE",
                        ticker=ticker,
                        is_primary=True,
                    )
                ],
                primary_exchange_code="BSE",
                currency="INR",
                country_code="IN",
                data_source="yfinance",
                data_source_id=yf_symbol,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            if not dry_run:
                await security.insert()
            count += 1

    logger.info("BSE: inserted %d securities", count)
    return count


async def seed_nse(dry_run: bool = False) -> int:
    """Read nse_stocks_list.json and upsert Security documents.

    Each entry: {"type": "NSE", "code": "20MICRONS", "name": "...", "description": "..."}
    Skip entries whose code ends with '_UADJ' (unadjusted duplicates).
    """
    if not NSE_JSON.exists():
        logger.warning("NSE JSON not found at %s – skipping", NSE_JSON)
        return 0

    with open(NSE_JSON, encoding="utf-8") as f:
        entries = json.load(f)

    count = 0
    for entry in entries:
        code = entry.get("code", "").strip()
        raw_name = entry.get("name", "").strip()

        if not code:
            continue
        # Skip unadjusted duplicates
        if code.endswith("_UADJ"):
            continue

        name = _clean_name(raw_name)
        symbol = code
        yf_symbol = f"{code}.NS"

        # Check for existing security to avoid duplicates
        existing = await Security.find_one(
            Security.symbol == symbol,
            Security.primary_exchange_code == "NSE",
        )
        if existing:
            continue

        security = Security(
            symbol=symbol,
            name=name or symbol,
            security_type=SecurityType.EQUITY,
            listings=[
                ExchangeListing(
                    exchange_code="NSE",
                    ticker=code,
                    is_primary=True,
                )
            ],
            primary_exchange_code="NSE",
            currency="INR",
            country_code="IN",
            data_source="yfinance",
            data_source_id=yf_symbol,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if not dry_run:
            await security.insert()
        count += 1

    logger.info("NSE: inserted %d securities", count)
    return count


async def main():
    logger.info("Initializing database connection...")
    await init_db()

    try:
        bse_count = await seed_bse()
        nse_count = await seed_nse()
        logger.info("Seeding complete. BSE: %d, NSE: %d, Total: %d", bse_count, nse_count, bse_count + nse_count)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
