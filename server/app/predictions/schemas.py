from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ml import ModelType


# ── Request schemas ──────────────────────────────────────────────────────────


class TrainRequest(BaseModel):
    epochs: int = Field(default=10, ge=1, le=200)
    batch_size: int = Field(default=32, ge=1, le=512)
    lookback_window: int = Field(default=60, ge=10, le=365)
    prediction_horizon: int = Field(default=1, ge=1, le=90)


# ── Response schemas ─────────────────────────────────────────────────────────


class TrainResponse(BaseModel):
    model_id: str
    status: str
    message: str


class PredictionPoint(BaseModel):
    date: date
    actual: Optional[float] = None
    predicted: float
    prediction_low: Optional[float] = None
    prediction_high: Optional[float] = None


class AccuracyMetrics(BaseModel):
    rmse: float
    mae: float
    mape: float
    directional_accuracy: float


class PredictionResponse(BaseModel):
    symbol: str
    model_type: ModelType
    predictions: list[PredictionPoint]
    metrics: AccuracyMetrics
    model_id: str
    trained_at: datetime


class ActualDataPoint(BaseModel):
    date: date
    close: float
    volume: int


class ActualDataResponse(BaseModel):
    symbol: str
    data: list[ActualDataPoint]
    count: int
