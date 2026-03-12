import logging
import uuid
from datetime import date, datetime, timezone

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.portfolio import (
    Holding,
    Portfolio,
    PortfolioSnapshot,
    Transaction,
    TransactionType,
)
from app.models.security import Security
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem

from .schemas import (
    AddHoldingRequest,
    AddWatchlistItemRequest,
    CreatePortfolioRequest,
    CreateWatchlistRequest,
    HoldingResponse,
    PortfolioDetailResponse,
    PortfolioSnapshotResponse,
    PortfolioSummary,
    RiskSettingsRequest,
    RiskSettingsResponse,
    SellHoldingRequest,
    TransactionResponse,
    UpdatePortfolioRequest,
    WatchlistItemResponse,
    WatchlistResponse,
)

logger = logging.getLogger(__name__)

MAX_PORTFOLIOS_PER_USER = 10
MAX_RECENT_TRANSACTIONS = 500


# ── Helpers ──────────────────────────────────────────────────────────────────


def _to_oid(value: str, label: str = "ID") -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label} format.",
        )


async def _get_portfolio_for_user(user_id: str, portfolio_id: str) -> Portfolio:
    oid = _to_oid(portfolio_id, "portfolio ID")
    portfolio = await Portfolio.get(oid)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found.",
        )
    if not portfolio.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found.",
        )
    return portfolio


async def _get_security(security_id: str) -> Security:
    oid = _to_oid(security_id, "security ID")
    security = await Security.get(oid)
    if security is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )
    return security


def _holding_to_response(h: Holding) -> HoldingResponse:
    return HoldingResponse(
        security_id=h.security_id,
        symbol=h.symbol,
        exchange_code=h.exchange_code,
        quantity=h.quantity,
        avg_buy_price=h.avg_buy_price,
        current_price=h.current_price,
        invested=h.invested_value,
        current_value=h.current_value,
        pnl=h.unrealized_pnl,
        pnl_pct=h.unrealized_pnl_pct,
        first_buy_date=h.first_buy_date,
        last_transaction_date=h.last_transaction_date,
    )


def _transaction_to_response(t: Transaction) -> TransactionResponse:
    return TransactionResponse(
        transaction_id=t.transaction_id,
        type=t.transaction_type.value,
        symbol=t.symbol,
        exchange_code=t.exchange_code,
        quantity=t.quantity,
        price=t.price,
        total=t.total_amount,
        fees=t.fees,
        taxes=t.taxes,
        net_amount=t.net_amount,
        currency=t.currency,
        executed_at=t.executed_at,
    )


def _portfolio_to_summary(p: Portfolio) -> PortfolioSummary:
    total_pnl = p.total_current_value - p.total_invested + p.total_realized_pnl
    total_pnl_pct = (
        (total_pnl / p.total_invested * 100) if p.total_invested > 0 else None
    )
    return PortfolioSummary(
        id=str(p.id),
        name=p.name,
        description=p.description,
        currency=p.currency,
        total_invested=p.total_invested,
        current_value=p.total_current_value,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        holding_count=len(p.holdings),
        cash_balance=p.cash_balance,
        created_at=p.created_at,
    )


def _portfolio_to_detail(p: Portfolio) -> PortfolioDetailResponse:
    return PortfolioDetailResponse(
        id=str(p.id),
        name=p.name,
        description=p.description,
        currency=p.currency,
        is_default=p.is_default,
        total_invested=p.total_invested,
        current_value=p.total_current_value,
        total_realized_pnl=p.total_realized_pnl,
        cash_balance=p.cash_balance,
        holding_count=len(p.holdings),
        transaction_count=p.transaction_count,
        holdings=[_holding_to_response(h) for h in p.holdings],
        recent_transactions=[
            _transaction_to_response(t) for t in p.recent_transactions
        ],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _recalculate_aggregates(portfolio: Portfolio) -> None:
    """Recalculate portfolio-level aggregates from holdings."""
    portfolio.total_invested = sum(h.invested_value for h in portfolio.holdings)
    portfolio.total_current_value = sum(
        h.current_value for h in portfolio.holdings if h.current_value is not None
    )


# ── Portfolio CRUD ───────────────────────────────────────────────────────────


async def create_portfolio(
    user_id: str, data: CreatePortfolioRequest
) -> PortfolioSummary:
    # Check limit
    count = await Portfolio.find(
        Portfolio.user_id == user_id, Portfolio.is_active == True
    ).count()
    if count >= MAX_PORTFOLIOS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_PORTFOLIOS_PER_USER} portfolios per user.",
        )

    is_default = count == 0  # First portfolio is default

    portfolio = Portfolio(
        user_id=user_id,
        name=data.name,
        description=data.description,
        currency=data.currency,
        cash_balance=data.initial_cash_balance,
        is_default=is_default,
    )
    await portfolio.insert()
    return _portfolio_to_summary(portfolio)


async def get_user_portfolios(user_id: str) -> list[PortfolioSummary]:
    portfolios = await Portfolio.find(
        Portfolio.user_id == user_id, Portfolio.is_active == True
    ).to_list()
    return [_portfolio_to_summary(p) for p in portfolios]


async def get_portfolio_detail(
    user_id: str, portfolio_id: str
) -> PortfolioDetailResponse:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)
    return _portfolio_to_detail(portfolio)


async def update_portfolio(
    user_id: str, portfolio_id: str, data: UpdatePortfolioRequest
) -> PortfolioSummary:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)

    if data.name is not None:
        portfolio.name = data.name
    if data.description is not None:
        portfolio.description = data.description

    portfolio.updated_at = datetime.now(timezone.utc)
    await portfolio.save()
    return _portfolio_to_summary(portfolio)


# ── Buy / Sell ───────────────────────────────────────────────────────────────


async def add_holding(
    user_id: str, portfolio_id: str, data: AddHoldingRequest
) -> PortfolioDetailResponse:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)
    security = await _get_security(data.security_id)

    total_cost = data.buy_price * data.quantity + data.fees + data.taxes

    # Check cash balance
    if total_cost > portfolio.cash_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient cash balance. Required: {total_cost:.2f}, "
                f"available: {portfolio.cash_balance:.2f}."
            ),
        )

    now = datetime.now(timezone.utc)
    today = date.today()

    # Find existing holding
    existing = next(
        (h for h in portfolio.holdings if h.security_id == data.security_id),
        None,
    )

    if existing:
        # Recalculate weighted average buy price
        total_old = existing.avg_buy_price * existing.quantity
        total_new = data.buy_price * data.quantity
        new_quantity = existing.quantity + data.quantity
        existing.avg_buy_price = (total_old + total_new) / new_quantity
        existing.quantity = new_quantity
        existing.invested_value = existing.avg_buy_price * existing.quantity
        existing.last_transaction_date = today
        # Update current value if we have a current price
        if existing.current_price is not None:
            existing.current_value = existing.current_price * existing.quantity
            existing.unrealized_pnl = existing.current_value - existing.invested_value
            if existing.invested_value > 0:
                existing.unrealized_pnl_pct = (
                    existing.unrealized_pnl / existing.invested_value * 100
                )
    else:
        # Create new holding
        current_price = (
            security.quote.last_price if security.quote else None
        )
        invested_value = data.buy_price * data.quantity
        current_value = (
            current_price * data.quantity if current_price is not None else None
        )
        unrealized_pnl = (
            current_value - invested_value
            if current_value is not None
            else None
        )
        unrealized_pnl_pct = (
            (unrealized_pnl / invested_value * 100)
            if unrealized_pnl is not None and invested_value > 0
            else None
        )
        holding = Holding(
            security_id=data.security_id,
            symbol=security.symbol,
            exchange_code=security.primary_exchange_code,
            quantity=data.quantity,
            avg_buy_price=data.buy_price,
            current_price=current_price,
            invested_value=invested_value,
            current_value=current_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            first_buy_date=today,
            last_transaction_date=today,
        )
        portfolio.holdings.append(holding)

    # Deduct from cash
    portfolio.cash_balance -= total_cost

    # Record transaction
    net_amount = data.buy_price * data.quantity + data.fees + data.taxes
    txn = Transaction(
        transaction_id=uuid.uuid4().hex,
        transaction_type=TransactionType.BUY,
        security_id=data.security_id,
        symbol=security.symbol,
        exchange_code=security.primary_exchange_code,
        quantity=data.quantity,
        price=data.buy_price,
        total_amount=data.buy_price * data.quantity,
        fees=data.fees,
        taxes=data.taxes,
        net_amount=net_amount,
        currency=portfolio.currency,
        executed_at=now,
    )
    portfolio.recent_transactions.insert(0, txn)
    if len(portfolio.recent_transactions) > MAX_RECENT_TRANSACTIONS:
        portfolio.recent_transactions = portfolio.recent_transactions[
            :MAX_RECENT_TRANSACTIONS
        ]
    portfolio.transaction_count += 1

    # Recalculate aggregates
    _recalculate_aggregates(portfolio)

    portfolio.updated_at = now
    await portfolio.save()

    return _portfolio_to_detail(portfolio)


async def sell_holding(
    user_id: str, portfolio_id: str, data: SellHoldingRequest
) -> PortfolioDetailResponse:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)
    security = await _get_security(data.security_id)

    # Find existing holding
    existing = next(
        (h for h in portfolio.holdings if h.security_id == data.security_id),
        None,
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No holding found for security '{data.security_id}'.",
        )

    if data.quantity > existing.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient quantity. Holding has {existing.quantity} shares, "
                f"trying to sell {data.quantity}."
            ),
        )

    now = datetime.now(timezone.utc)
    today = date.today()

    # Calculate realized P&L
    realized_pnl = (data.sell_price - existing.avg_buy_price) * data.quantity

    # Update or remove holding
    if data.quantity == existing.quantity:
        portfolio.holdings = [
            h for h in portfolio.holdings if h.security_id != data.security_id
        ]
    else:
        existing.quantity -= data.quantity
        existing.invested_value = existing.avg_buy_price * existing.quantity
        existing.last_transaction_date = today
        if existing.current_price is not None:
            existing.current_value = existing.current_price * existing.quantity
            existing.unrealized_pnl = (
                existing.current_value - existing.invested_value
            )
            if existing.invested_value > 0:
                existing.unrealized_pnl_pct = (
                    existing.unrealized_pnl / existing.invested_value * 100
                )

    # Add proceeds to cash (sell_price * quantity minus fees and taxes)
    proceeds = data.sell_price * data.quantity - data.fees - data.taxes
    portfolio.cash_balance += proceeds

    # Record realized P&L
    portfolio.total_realized_pnl += realized_pnl

    # Record transaction
    total_amount = data.sell_price * data.quantity
    net_amount = total_amount - data.fees - data.taxes
    txn = Transaction(
        transaction_id=uuid.uuid4().hex,
        transaction_type=TransactionType.SELL,
        security_id=data.security_id,
        symbol=security.symbol,
        exchange_code=security.primary_exchange_code,
        quantity=data.quantity,
        price=data.sell_price,
        total_amount=total_amount,
        fees=data.fees,
        taxes=data.taxes,
        net_amount=net_amount,
        currency=portfolio.currency,
        executed_at=now,
    )
    portfolio.recent_transactions.insert(0, txn)
    if len(portfolio.recent_transactions) > MAX_RECENT_TRANSACTIONS:
        portfolio.recent_transactions = portfolio.recent_transactions[
            :MAX_RECENT_TRANSACTIONS
        ]
    portfolio.transaction_count += 1

    # Recalculate aggregates
    _recalculate_aggregates(portfolio)

    portfolio.updated_at = now
    await portfolio.save()

    return _portfolio_to_detail(portfolio)


# ── Risk settings ────────────────────────────────────────────────────────────


async def get_risk_settings(user_id: str) -> RiskSettingsResponse:
    oid = _to_oid(user_id, "user ID")
    user = await User.get(oid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    rp = user.risk_profile
    return RiskSettingsResponse(
        high_pct=rp.high_pct,
        medium_pct=rp.medium_pct,
        low_pct=rp.low_pct,
        max_daily_trade_amount=rp.max_daily_trade_amount,
        preferred_currency=rp.preferred_currency,
    )


async def update_risk_settings(
    user_id: str, data: RiskSettingsRequest
) -> RiskSettingsResponse:
    oid = _to_oid(user_id, "user ID")
    user = await User.get(oid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.risk_profile.high_pct = data.high_pct
    user.risk_profile.medium_pct = data.medium_pct
    user.risk_profile.low_pct = data.low_pct
    user.risk_profile.max_daily_trade_amount = data.max_daily_trade_amount
    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    rp = user.risk_profile
    return RiskSettingsResponse(
        high_pct=rp.high_pct,
        medium_pct=rp.medium_pct,
        low_pct=rp.low_pct,
        max_daily_trade_amount=rp.max_daily_trade_amount,
        preferred_currency=rp.preferred_currency,
    )


# ── Portfolio snapshots ──────────────────────────────────────────────────────


async def take_portfolio_snapshot(
    user_id: str, portfolio_id: str
) -> PortfolioSnapshotResponse:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)

    today = date.today()

    # Check if snapshot for today already exists
    existing_snapshot = next(
        (s for s in portfolio.snapshots if s.date == today), None
    )
    if existing_snapshot:
        # Update existing snapshot
        existing_snapshot.total_invested = portfolio.total_invested
        existing_snapshot.total_current_value = portfolio.total_current_value
        existing_snapshot.total_realized_pnl = portfolio.total_realized_pnl
        existing_snapshot.total_unrealized_pnl = (
            portfolio.total_current_value - portfolio.total_invested
        )
        existing_snapshot.holding_count = len(portfolio.holdings)
        existing_snapshot.cash_balance = portfolio.cash_balance
        snapshot = existing_snapshot
    else:
        snapshot = PortfolioSnapshot(
            date=today,
            total_invested=portfolio.total_invested,
            total_current_value=portfolio.total_current_value,
            total_realized_pnl=portfolio.total_realized_pnl,
            total_unrealized_pnl=(
                portfolio.total_current_value - portfolio.total_invested
            ),
            holding_count=len(portfolio.holdings),
            cash_balance=portfolio.cash_balance,
        )
        portfolio.snapshots.append(snapshot)

    portfolio.updated_at = datetime.now(timezone.utc)
    await portfolio.save()

    return PortfolioSnapshotResponse(
        date=snapshot.date,
        total_invested=snapshot.total_invested,
        current_value=snapshot.total_current_value,
        realized_pnl=snapshot.total_realized_pnl,
        unrealized_pnl=snapshot.total_unrealized_pnl,
        holding_count=snapshot.holding_count,
        cash_balance=snapshot.cash_balance,
    )


async def get_portfolio_history(
    user_id: str, portfolio_id: str
) -> list[PortfolioSnapshotResponse]:
    portfolio = await _get_portfolio_for_user(user_id, portfolio_id)
    return [
        PortfolioSnapshotResponse(
            date=s.date,
            total_invested=s.total_invested,
            current_value=s.total_current_value,
            realized_pnl=s.total_realized_pnl,
            unrealized_pnl=s.total_unrealized_pnl,
            holding_count=s.holding_count,
            cash_balance=s.cash_balance,
        )
        for s in sorted(portfolio.snapshots, key=lambda x: x.date)
    ]


# ── Watchlist CRUD ───────────────────────────────────────────────────────────


async def create_watchlist(
    user_id: str, data: CreateWatchlistRequest
) -> WatchlistResponse:
    # Check if a watchlist with this name already exists for the user
    existing = await Watchlist.find_one(
        Watchlist.user_id == user_id, Watchlist.name == data.name
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Watchlist with name '{data.name}' already exists.",
        )

    # First watchlist is default
    count = await Watchlist.find(Watchlist.user_id == user_id).count()
    is_default = count == 0

    watchlist = Watchlist(
        user_id=user_id,
        name=data.name,
        is_default=is_default,
    )
    await watchlist.insert()
    return _watchlist_to_response(watchlist)


async def get_user_watchlists(user_id: str) -> list[WatchlistResponse]:
    watchlists = await Watchlist.find(
        Watchlist.user_id == user_id
    ).to_list()
    return [_watchlist_to_response(w) for w in watchlists]


async def add_watchlist_item(
    user_id: str, watchlist_id: str, data: AddWatchlistItemRequest
) -> WatchlistResponse:
    oid = _to_oid(watchlist_id, "watchlist ID")
    watchlist = await Watchlist.get(oid)
    if watchlist is None or watchlist.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found.",
        )

    # Look up the security to get symbol and exchange
    security = await _get_security(data.security_id)

    # Check if already in watchlist
    if any(item.security_id == data.security_id for item in watchlist.items):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Security is already in this watchlist.",
        )

    item = WatchlistItem(
        security_id=data.security_id,
        symbol=security.symbol,
        exchange_code=security.primary_exchange_code,
        notes=data.notes,
        alert_above=data.alert_above,
        alert_below=data.alert_below,
    )
    watchlist.items.append(item)
    watchlist.updated_at = datetime.now(timezone.utc)
    await watchlist.save()

    return _watchlist_to_response(watchlist)


async def remove_watchlist_item(
    user_id: str, watchlist_id: str, security_id: str
) -> WatchlistResponse:
    oid = _to_oid(watchlist_id, "watchlist ID")
    watchlist = await Watchlist.get(oid)
    if watchlist is None or watchlist.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found.",
        )

    original_count = len(watchlist.items)
    watchlist.items = [
        item for item in watchlist.items if item.security_id != security_id
    ]
    if len(watchlist.items) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found in this watchlist.",
        )

    watchlist.updated_at = datetime.now(timezone.utc)
    await watchlist.save()

    return _watchlist_to_response(watchlist)


def _watchlist_to_response(w: Watchlist) -> WatchlistResponse:
    return WatchlistResponse(
        id=str(w.id),
        name=w.name,
        is_default=w.is_default,
        items=[
            WatchlistItemResponse(
                security_id=item.security_id,
                symbol=item.symbol,
                exchange_code=item.exchange_code,
                added_at=item.added_at,
                notes=item.notes,
                alert_above=item.alert_above,
                alert_below=item.alert_below,
            )
            for item in w.items
        ],
        item_count=len(w.items),
        created_at=w.created_at,
        updated_at=w.updated_at,
    )
