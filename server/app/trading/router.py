"""Trading API router.

Endpoints:
- GET  /{security_id}/historic-signals  – SMA crossover signals on daily data
- POST /{security_id}/simulate          – run intraday simulation
- WS   /ws/trading/{security_id}        – stream simulation ticks in real-time
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.trading.schemas import HistoricSignalsResponse, SimulateRequest, SimulationResult
from app.trading.service import (
    get_historic_signals,
    run_trading_simulation,
    stream_simulation,
    ws_manager,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{security_id}/historic-signals",
    response_model=HistoricSignalsResponse,
    summary="Get SMA crossover signals on historical daily data",
)
async def historic_signals(
    security_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await get_historic_signals(security_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{security_id}/simulate",
    response_model=SimulationResult,
    summary="Run an intraday trading simulation",
)
async def simulate_trading(
    security_id: str,
    body: SimulateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await run_trading_simulation(
            security_id=security_id,
            user_id=str(current_user.id),
            profit_pct=body.profit_pct,
            loss_pct=body.loss_pct,
            ticks=body.ticks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/ws/trading/{security_id}")
async def ws_trading(
    websocket: WebSocket,
    security_id: str,
    profit_pct: float = Query(default=2.0),
    loss_pct: float = Query(default=2.0),
    ticks: int = Query(default=400),
):
    """Stream a live trading simulation over WebSocket.

    Connect to ``/api/v1/trading/ws/trading/{security_id}?profit_pct=2&loss_pct=2&ticks=400``.

    The server will send JSON messages with ``type`` = ``"tick"`` for each
    simulated price tick and a final ``type`` = ``"summary"`` message at the
    end.
    """
    await ws_manager.connect(websocket, security_id)
    try:
        await stream_simulation(
            websocket=websocket,
            security_id=security_id,
            profit_pct=profit_pct,
            loss_pct=loss_pct,
            ticks=ticks,
        )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "detail": str(exc)})
        except Exception:
            pass
    finally:
        ws_manager.disconnect(websocket, security_id)
