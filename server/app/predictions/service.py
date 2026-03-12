import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.config import settings
from app.models.ml import MLModel, MLPrediction, ModelStatus, ModelType, PredictionStatus
from app.models.price_history import PriceHistoryDaily
from app.models.security import Security

from .ml.lstm_model import LSTMPricePredictor, predict, train_model
from .ml.model_cache import save_model as cache_save_model
from .ml.preprocessing import create_sequences, prepare_features, scale_data
from .schemas import (
    AccuracyMetrics,
    ActualDataPoint,
    ActualDataResponse,
    PredictionPoint,
    PredictionResponse,
    TrainRequest,
    TrainResponse,
)

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _resolve_security(security_id: str) -> Security:
    """Look up a Security by its ObjectId, raising 400/404 as appropriate."""
    try:
        oid = PydanticObjectId(security_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security ID format.",
        )

    sec = await Security.get(oid)
    if sec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security '{security_id}' not found.",
        )
    return sec


async def _fetch_price_history(security_id: str, days: int) -> list[PriceHistoryDaily]:
    """Fetch the most recent *days* of daily price records for the given security."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = (
        await PriceHistoryDaily.find(
            PriceHistoryDaily.security_id == security_id,
            PriceHistoryDaily.date >= cutoff.date(),
        )
        .sort("+date")
        .to_list()
    )
    return records


def _records_to_dataframe(records: list[PriceHistoryDaily]) -> pd.DataFrame:
    """Convert a list of PriceHistoryDaily documents to a pandas DataFrame."""
    rows = []
    for r in records:
        rows.append(
            {
                "Date": r.date,
                "Open": r.open,
                "High": r.high,
                "Low": r.low,
                "Close": r.close,
                "Volume": r.volume,
            }
        )
    df = pd.DataFrame(rows)
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    return df


def _calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> AccuracyMetrics:
    """Calculate RMSE, MAE, MAPE and directional accuracy."""
    # RMSE
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))

    # MAE
    mae = float(np.mean(np.abs(actual - predicted)))

    # MAPE (avoid division by zero)
    nonzero_mask = actual != 0
    if nonzero_mask.any():
        mape = float(np.mean(np.abs((actual[nonzero_mask] - predicted[nonzero_mask]) / actual[nonzero_mask])) * 100)
    else:
        mape = 0.0

    # Directional accuracy: % of days where predicted direction matches actual
    if len(actual) > 1:
        actual_direction = np.diff(actual) > 0
        predicted_direction = np.diff(predicted) > 0
        directional_accuracy = float(np.mean(actual_direction == predicted_direction) * 100)
    else:
        directional_accuracy = 0.0

    return AccuracyMetrics(
        rmse=round(rmse, 4),
        mae=round(mae, 4),
        mape=round(mape, 4),
        directional_accuracy=round(directional_accuracy, 2),
    )


# ── Public service functions ─────────────────────────────────────────────────


async def get_actual_data(security_id: str, days: int = 365) -> ActualDataResponse:
    """Return raw historical close/volume data for the security."""
    sec = await _resolve_security(security_id)
    records = await _fetch_price_history(security_id, days)

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price history found for this security. Fetch historical data first.",
        )

    data_points = [
        ActualDataPoint(date=r.date, close=r.close, volume=r.volume)
        for r in records
    ]

    return ActualDataResponse(
        symbol=sec.symbol,
        data=data_points,
        count=len(data_points),
    )


def _run_training(
    df: pd.DataFrame,
    params: TrainRequest,
) -> dict:
    """Synchronous, CPU-bound training work.

    This will be called via asyncio.to_thread() so it must not touch the
    event loop or any async DB calls.
    """
    start_time = time.time()

    # 1. Prepare features
    featured = prepare_features(df)

    # 2. Extract close prices and scale
    close_values = featured["Close"].values
    scaled_close, scaler = scale_data(close_values)

    # 3. Create sequences
    X, y = create_sequences(scaled_close, lookback_window=params.lookback_window)

    if len(X) < 10:
        raise ValueError(
            f"Not enough data to train. Have {len(X)} samples after "
            f"creating sequences with lookback={params.lookback_window}. "
            f"Need at least 10."
        )

    # 4. Split 80/20
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # 5. Train
    model, loss_history = train_model(
        X_train,
        y_train,
        epochs=params.epochs,
        batch_size=params.batch_size,
    )

    # 6. Predict on test set
    predictions = predict(model, X_test, scaler)

    # 7. Get actual values (inverse-scaled)
    actual_values = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

    # 8. Calculate prediction bounds (simple +/- 1 std of residuals)
    residuals = actual_values - predictions
    residual_std = float(np.std(residuals))

    duration = time.time() - start_time

    return {
        "model": model,
        "scaler": scaler,
        "predictions": predictions,
        "actual_values": actual_values,
        "residual_std": residual_std,
        "loss_history": loss_history,
        "split_idx": split_idx,
        "lookback_window": params.lookback_window,
        "training_duration": duration,
        "training_samples": len(X_train),
    }


async def train_prediction_model(
    security_id: str,
    params: Optional[TrainRequest] = None,
) -> TrainResponse:
    """Train an LSTM model for the given security and cache results."""
    if params is None:
        params = TrainRequest()

    sec = await _resolve_security(security_id)

    # Fetch historical data
    records = await _fetch_price_history(security_id, days=365 * 3)

    min_required = params.lookback_window + 50  # need enough for sequences + train/test split
    if len(records) < min_required:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Not enough price data to train. Have {len(records)} records, "
                f"need at least {min_required}. Fetch historical data first."
            ),
        )

    df = _records_to_dataframe(records)

    # Create MLModel record (status=TRAINING)
    ml_model = MLModel(
        name=f"LSTM_{sec.symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        model_type=ModelType.LSTM_PRICE,
        version="1.0",
        status=ModelStatus.TRAINING,
        target_security_id=security_id,
        target_description=f"Close price prediction for {sec.symbol}",
        prediction_horizon=f"{params.prediction_horizon}d",
        hyperparameters={
            "epochs": params.epochs,
            "batch_size": params.batch_size,
            "lookback_window": params.lookback_window,
            "prediction_horizon": params.prediction_horizon,
            "lr": 0.001,
            "hidden_size": 50,
            "num_layers": 2,
            "dropout": 0.2,
        },
        feature_columns=["Close", "HL_PCT", "PCT_change", "Volume"],
        training_data_from=datetime.combine(records[0].date, datetime.min.time()) if records else None,
        training_data_to=datetime.combine(records[-1].date, datetime.min.time()) if records else None,
    )
    await ml_model.insert()
    model_id = str(ml_model.id)

    try:
        # Run training in a thread (CPU-bound work)
        result = await asyncio.to_thread(_run_training, df, params)

        # Save model artifacts to disk
        model_path, scaler_path = cache_save_model(
            result["model"],
            result["scaler"],
            model_id,
            settings.model_cache_dir,
        )

        # Calculate metrics
        metrics = _calculate_metrics(result["actual_values"], result["predictions"])

        # Update MLModel record
        ml_model.status = ModelStatus.TRAINED
        ml_model.training_samples = result["training_samples"]
        ml_model.training_duration_seconds = result["training_duration"]
        ml_model.model_artifact_path = model_path
        ml_model.scaler_artifact_path = scaler_path
        ml_model.metrics = {
            "rmse": metrics.rmse,
            "mae": metrics.mae,
            "mape": metrics.mape,
            "directional_accuracy": metrics.directional_accuracy,
            "final_train_loss": result["loss_history"][-1] if result["loss_history"] else None,
        }
        ml_model.updated_at = datetime.utcnow()
        await ml_model.save()

        # Store prediction records in MongoDB
        # Map predictions back to dates: the test set starts at
        # split_idx + lookback_window in the original dataframe
        dates = list(df.index)
        test_start_date_idx = result["split_idx"] + result["lookback_window"]

        prediction_records = []
        now = datetime.utcnow()
        for i, pred_val in enumerate(result["predictions"]):
            date_idx = test_start_date_idx + i
            if date_idx < len(dates):
                pred_date = dates[date_idx]
            else:
                # Should not happen, but handle gracefully
                pred_date = dates[-1]

            actual_val = float(result["actual_values"][i])
            pred_float = float(pred_val)
            residual_std = result["residual_std"]

            record = MLPrediction(
                model_id=model_id,
                security_id=security_id,
                symbol=sec.symbol,
                prediction_date=now,
                target_date=datetime.combine(pred_date, datetime.min.time()) if hasattr(pred_date, "year") else pred_date,
                predicted_value=pred_float,
                prediction_low=pred_float - residual_std,
                prediction_high=pred_float + residual_std,
                actual_value=actual_val,
                prediction_error=abs(actual_val - pred_float),
                status=PredictionStatus.EVALUATED,
            )
            prediction_records.append(record)

        if prediction_records:
            await MLPrediction.insert_many(prediction_records)

        return TrainResponse(
            model_id=model_id,
            status="trained",
            message=(
                f"Model trained successfully on {result['training_samples']} samples. "
                f"RMSE: {metrics.rmse:.4f}, MAE: {metrics.mae:.4f}, "
                f"Directional accuracy: {metrics.directional_accuracy:.1f}%"
            ),
        )

    except Exception as exc:
        # Mark model as failed
        ml_model.status = ModelStatus.FAILED
        ml_model.metrics = {"error": str(exc)}
        ml_model.updated_at = datetime.utcnow()
        await ml_model.save()

        logger.exception("Training failed for security %s", security_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {exc}",
        )


async def get_predictions(security_id: str) -> PredictionResponse:
    """Retrieve cached predictions from the most recent trained model."""
    sec = await _resolve_security(security_id)

    # Find the most recent successfully trained model for this security
    ml_model = await MLModel.find_one(
        MLModel.target_security_id == security_id,
        MLModel.model_type == ModelType.LSTM_PRICE,
        MLModel.status.in_([ModelStatus.TRAINED, ModelStatus.DEPLOYED]),
    ).sort("-created_at")

    if ml_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trained model found for this security. Train a model first via POST /train.",
        )

    model_id = str(ml_model.id)

    # Fetch predictions for this model
    prediction_records = (
        await MLPrediction.find(
            MLPrediction.model_id == model_id,
            MLPrediction.security_id == security_id,
        )
        .sort("+target_date")
        .to_list()
    )

    if not prediction_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction records found for the trained model.",
        )

    prediction_points = [
        PredictionPoint(
            date=p.target_date.date() if isinstance(p.target_date, datetime) else p.target_date,
            actual=p.actual_value,
            predicted=p.predicted_value,
            prediction_low=p.prediction_low,
            prediction_high=p.prediction_high,
        )
        for p in prediction_records
    ]

    # Build metrics from stored model
    stored_metrics = ml_model.metrics or {}
    metrics = AccuracyMetrics(
        rmse=stored_metrics.get("rmse", 0.0),
        mae=stored_metrics.get("mae", 0.0),
        mape=stored_metrics.get("mape", 0.0),
        directional_accuracy=stored_metrics.get("directional_accuracy", 0.0),
    )

    return PredictionResponse(
        symbol=sec.symbol,
        model_type=ml_model.model_type,
        predictions=prediction_points,
        metrics=metrics,
        model_id=model_id,
        trained_at=ml_model.created_at,
    )


async def get_model_evaluation(security_id: str) -> dict:
    """Return detailed evaluation metrics for the latest trained model."""
    sec = await _resolve_security(security_id)

    ml_model = await MLModel.find_one(
        MLModel.target_security_id == security_id,
        MLModel.model_type == ModelType.LSTM_PRICE,
        MLModel.status.in_([ModelStatus.TRAINED, ModelStatus.DEPLOYED]),
    ).sort("-created_at")

    if ml_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trained model found for this security.",
        )

    return {
        "model_id": str(ml_model.id),
        "model_name": ml_model.name,
        "model_type": ml_model.model_type.value,
        "status": ml_model.status.value,
        "symbol": sec.symbol,
        "metrics": ml_model.metrics,
        "hyperparameters": ml_model.hyperparameters,
        "training_samples": ml_model.training_samples,
        "training_duration_seconds": ml_model.training_duration_seconds,
        "training_data_from": ml_model.training_data_from.isoformat() if ml_model.training_data_from else None,
        "training_data_to": ml_model.training_data_to.isoformat() if ml_model.training_data_to else None,
        "feature_columns": ml_model.feature_columns,
        "trained_at": ml_model.created_at.isoformat(),
    }
