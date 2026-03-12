from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.auth.router import router as auth_router
from app.securities.router import router as securities_router
from app.predictions.router import router as predictions_router
from app.trading.router import router as trading_router
from app.portfolio.router import router as portfolio_router
from app.trading.service import stream_simulation, ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Gloria Trade API",
    description="AI-powered trading platform - Profit & Glory",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(securities_router, prefix="/api/v1/securities", tags=["securities"])
app.include_router(predictions_router, prefix="/api/v1/predictions", tags=["predictions"])
app.include_router(trading_router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["portfolio"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


# Top-level WebSocket endpoint for trading simulation streaming
@app.websocket("/ws/trading/{security_id}")
async def ws_trading_root(
    websocket: WebSocket,
    security_id: str,
    profit_pct: float = Query(default=2.0),
    loss_pct: float = Query(default=2.0),
    ticks: int = Query(default=400),
):
    """Stream a live trading simulation over WebSocket.

    Connect to ``ws://<host>/ws/trading/{security_id}?profit_pct=2&loss_pct=2&ticks=400``.
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
