from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.models.user import User

from .schemas import (
    AddHoldingRequest,
    AddWatchlistItemRequest,
    CreatePortfolioRequest,
    CreateWatchlistRequest,
    PortfolioDetailResponse,
    PortfolioSnapshotResponse,
    PortfolioSummary,
    RiskSettingsRequest,
    RiskSettingsResponse,
    SellHoldingRequest,
    UpdatePortfolioRequest,
    WatchlistResponse,
)
from .service import (
    add_holding,
    add_watchlist_item,
    create_portfolio,
    create_watchlist,
    get_portfolio_detail,
    get_portfolio_history,
    get_risk_settings,
    get_user_portfolios,
    get_user_watchlists,
    remove_watchlist_item,
    sell_holding,
    take_portfolio_snapshot,
    update_portfolio,
    update_risk_settings,
)

router = APIRouter()


# ── Risk settings ────────────────────────────────────────────────────────────


@router.get("/settings/risk", response_model=RiskSettingsResponse)
async def get_risk_settings_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
) -> RiskSettingsResponse:
    """Get the current user's risk allocation settings."""
    return await get_risk_settings(str(current_user.id))


@router.put("/settings/risk", response_model=RiskSettingsResponse)
async def update_risk_settings_endpoint(
    data: RiskSettingsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RiskSettingsResponse:
    """Update the current user's risk allocation settings.

    Percentages (high_pct, medium_pct, low_pct) must sum to exactly 100.
    """
    return await update_risk_settings(str(current_user.id), data)


# ── Watchlists ───────────────────────────────────────────────────────────────


@router.get("/watchlists", response_model=list[WatchlistResponse])
async def list_watchlists_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[WatchlistResponse]:
    """List all watchlists for the current user."""
    return await get_user_watchlists(str(current_user.id))


@router.post(
    "/watchlists",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_watchlist_endpoint(
    data: CreateWatchlistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> WatchlistResponse:
    """Create a new watchlist."""
    return await create_watchlist(str(current_user.id), data)


@router.post(
    "/watchlists/{watchlist_id}/items",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_watchlist_item_endpoint(
    watchlist_id: str,
    data: AddWatchlistItemRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> WatchlistResponse:
    """Add a security to a watchlist."""
    return await add_watchlist_item(str(current_user.id), watchlist_id, data)


@router.delete(
    "/watchlists/{watchlist_id}/items/{security_id}",
    response_model=WatchlistResponse,
)
async def remove_watchlist_item_endpoint(
    watchlist_id: str,
    security_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> WatchlistResponse:
    """Remove a security from a watchlist."""
    return await remove_watchlist_item(
        str(current_user.id), watchlist_id, security_id
    )


# ── Portfolios ───────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PortfolioSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio_endpoint(
    data: CreatePortfolioRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioSummary:
    """Create a new portfolio. Maximum 10 per user."""
    return await create_portfolio(str(current_user.id), data)


@router.get("", response_model=list[PortfolioSummary])
async def list_portfolios_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[PortfolioSummary]:
    """List all portfolios for the current user."""
    return await get_user_portfolios(str(current_user.id))


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio_detail_endpoint(
    portfolio_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioDetailResponse:
    """Get full details for a specific portfolio including holdings and transactions."""
    return await get_portfolio_detail(str(current_user.id), portfolio_id)


@router.patch("/{portfolio_id}", response_model=PortfolioSummary)
async def update_portfolio_endpoint(
    portfolio_id: str,
    data: UpdatePortfolioRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioSummary:
    """Update portfolio name and/or description."""
    return await update_portfolio(str(current_user.id), portfolio_id, data)


@router.post(
    "/{portfolio_id}/buy",
    response_model=PortfolioDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def buy_holding_endpoint(
    portfolio_id: str,
    data: AddHoldingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioDetailResponse:
    """Buy shares of a security. Deducts from cash balance and creates a transaction."""
    return await add_holding(str(current_user.id), portfolio_id, data)


@router.post(
    "/{portfolio_id}/sell",
    response_model=PortfolioDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sell_holding_endpoint(
    portfolio_id: str,
    data: SellHoldingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioDetailResponse:
    """Sell shares of a security. Adds proceeds to cash balance and records realized P&L."""
    return await sell_holding(str(current_user.id), portfolio_id, data)


@router.get(
    "/{portfolio_id}/history",
    response_model=list[PortfolioSnapshotResponse],
)
async def get_portfolio_history_endpoint(
    portfolio_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[PortfolioSnapshotResponse]:
    """Get portfolio value snapshots over time for charting."""
    return await get_portfolio_history(str(current_user.id), portfolio_id)


@router.post(
    "/{portfolio_id}/snapshot",
    response_model=PortfolioSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def take_snapshot_endpoint(
    portfolio_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> PortfolioSnapshotResponse:
    """Manually trigger a portfolio snapshot for the current day."""
    return await take_portfolio_snapshot(str(current_user.id), portfolio_id)
