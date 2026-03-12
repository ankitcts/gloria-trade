from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.models.user import User

from .schemas import (
    ActualDataResponse,
    PredictionResponse,
    TrainRequest,
    TrainResponse,
)
from .service import (
    get_actual_data,
    get_model_evaluation,
    get_predictions,
    train_prediction_model,
)

router = APIRouter()


@router.get("/{security_id}/actual", response_model=ActualDataResponse)
async def actual_data_endpoint(
    security_id: str,
    days: int = Query(default=365, ge=1, le=3650, description="Number of days of history"),
    _user: User = Depends(get_current_user),
):
    """Get actual historical price data for a security."""
    return await get_actual_data(security_id, days=days)


@router.get("/{security_id}/evaluate")
async def evaluate_endpoint(
    security_id: str,
    _user: User = Depends(get_current_user),
):
    """Get detailed accuracy metrics for the latest trained model."""
    return await get_model_evaluation(security_id)


@router.post("/{security_id}/train", response_model=TrainResponse)
async def train_endpoint(
    security_id: str,
    body: Optional[TrainRequest] = None,
    _user: User = Depends(get_current_user),
):
    """Trigger LSTM model training for a security.

    Accepts optional training parameters (epochs, batch_size, lookback_window,
    prediction_horizon).  Defaults: epochs=10, batch_size=32, lookback=60, horizon=1.

    Training runs in a background thread so it does not block the event loop,
    but the response is returned only after training completes.
    """
    return await train_prediction_model(security_id, params=body)


@router.get("/{security_id}", response_model=PredictionResponse)
async def predictions_endpoint(
    security_id: str,
    _user: User = Depends(get_current_user),
):
    """Get cached LSTM predictions for a security (from the most recent trained model)."""
    return await get_predictions(security_id)
