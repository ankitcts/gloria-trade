import logging
import pickle
import time
from pathlib import Path
from typing import Optional

import torch
from sklearn.preprocessing import MinMaxScaler

from .lstm_model import LSTMPricePredictor

logger = logging.getLogger(__name__)


def _ensure_dir(cache_dir: str) -> Path:
    path = Path(cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_model(
    model: LSTMPricePredictor,
    scaler: MinMaxScaler,
    model_id: str,
    cache_dir: str,
) -> tuple[str, str]:
    """Persist the trained model and scaler to disk.

    Returns
    -------
    (model_path, scaler_path) : tuple[str, str]
        Absolute paths to the saved artifacts.
    """
    base = _ensure_dir(cache_dir)

    model_path = base / f"{model_id}.pt"
    scaler_path = base / f"{model_id}_scaler.pkl"

    torch.save(model.state_dict(), str(model_path))

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    logger.info("Saved model artifacts: %s, %s", model_path, scaler_path)
    return str(model_path), str(scaler_path)


def load_model(
    model_id: str,
    cache_dir: str,
    input_size: int = 1,
) -> Optional[tuple[LSTMPricePredictor, MinMaxScaler]]:
    """Load a cached model and scaler from disk.

    Returns None if artifacts are not found.
    """
    base = Path(cache_dir)
    model_path = base / f"{model_id}.pt"
    scaler_path = base / f"{model_id}_scaler.pkl"

    if not model_path.exists() or not scaler_path.exists():
        return None

    model = LSTMPricePredictor(input_size=input_size)
    model.load_state_dict(torch.load(str(model_path), map_location="cpu", weights_only=True))
    model.eval()

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    logger.info("Loaded cached model: %s", model_id)
    return model, scaler


def is_model_cached(model_id: str, cache_dir: str) -> bool:
    """Check whether model artifacts exist on disk."""
    base = Path(cache_dir)
    return (base / f"{model_id}.pt").exists() and (base / f"{model_id}_scaler.pkl").exists()


def clear_old_models(cache_dir: str, max_age_hours: int) -> int:
    """Remove model artifacts older than *max_age_hours*.

    Returns the number of files removed.
    """
    base = Path(cache_dir)
    if not base.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0

    for fpath in base.iterdir():
        if fpath.suffix in (".pt", ".pkl") and fpath.stat().st_mtime < cutoff:
            try:
                fpath.unlink()
                removed += 1
                logger.info("Removed expired artifact: %s", fpath.name)
            except OSError as exc:
                logger.warning("Failed to remove %s: %s", fpath.name, exc)

    return removed
