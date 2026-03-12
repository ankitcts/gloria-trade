from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ModelType(str, Enum):
    LSTM_PRICE = "lstm_price"
    LINEAR_REGRESSION = "linear_regression"
    SVM_CLASSIFIER = "svm_classifier"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class MLModel(Document):
    name: Indexed(str)
    model_type: ModelType
    version: str
    status: Indexed(ModelStatus)

    target_security_id: Optional[str] = None
    target_description: str
    prediction_horizon: str

    training_data_from: Optional[datetime] = None
    training_data_to: Optional[datetime] = None
    training_samples: Optional[int] = None
    training_duration_seconds: Optional[float] = None

    hyperparameters: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    feature_columns: list[str] = Field(default_factory=list)

    model_artifact_path: Optional[str] = None
    scaler_artifact_path: Optional[str] = None

    trained_by: Optional[str] = None
    deployed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "ml_models"
        indexes = [
            [("target_security_id", 1), ("model_type", 1), ("status", 1)],
            [("status", 1)],
        ]


class PredictionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EVALUATED = "evaluated"


class MLPrediction(Document):
    model_id: Indexed(str)
    security_id: Indexed(str)
    symbol: Optional[str] = None

    prediction_date: Indexed(datetime)
    target_date: datetime

    predicted_value: float
    prediction_low: Optional[float] = None
    prediction_high: Optional[float] = None
    confidence: Optional[float] = None

    signal: Optional[str] = None
    signal_strength: Optional[float] = None

    risk_assessment: Optional[dict] = None

    actual_value: Optional[float] = None
    prediction_error: Optional[float] = None
    status: PredictionStatus = PredictionStatus.ACTIVE

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "ml_predictions"
        indexes = [
            [("security_id", 1), ("prediction_date", -1)],
            [("model_id", 1), ("prediction_date", -1)],
            [("status", 1), ("target_date", 1)],
        ]
