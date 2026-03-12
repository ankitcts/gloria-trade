import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features from raw OHLCV data.

    Expects columns: Open, High, Low, Close, Volume (case-insensitive -- will
    be normalised internally).  Returns a DataFrame with:
        Close, HL_PCT, PCT_change, Volume (normalised)
    """
    # Normalise column names to title-case so the function is resilient to
    # varying capitalisation coming from different data sources.
    col_map = {c: c.title() for c in df.columns}
    df = df.rename(columns=col_map)

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = pd.DataFrame(index=df.index)
    result["Close"] = df["Close"].astype(float)
    result["HL_PCT"] = (df["High"].astype(float) - df["Low"].astype(float)) / df["Close"].astype(float) * 100.0
    result["PCT_change"] = (df["Close"].astype(float) - df["Open"].astype(float)) / df["Open"].astype(float) * 100.0

    # Normalise volume to 0-1 range within the dataset
    vol = df["Volume"].astype(float)
    vol_max = vol.max()
    result["Volume"] = vol / vol_max if vol_max > 0 else vol

    result.fillna(0, inplace=True)
    return result


def create_sequences(
    data: np.ndarray,
    lookback_window: int = 60,
) -> tuple[np.ndarray, np.ndarray]:
    """Create input/output sequences for LSTM training.

    Parameters
    ----------
    data : np.ndarray
        1-D array of scaled values (typically the Close price).
    lookback_window : int
        Number of past time-steps to use as input.

    Returns
    -------
    X : np.ndarray of shape (samples, lookback_window, 1)
    y : np.ndarray of shape (samples,)
    """
    X, y = [], []
    for i in range(lookback_window, len(data)):
        X.append(data[i - lookback_window : i])
        y.append(data[i])

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    # Reshape X to (samples, lookback_window, 1) for LSTM
    if X.ndim == 2:
        X = X.reshape(X.shape[0], X.shape[1], 1)

    return X, y


def scale_data(
    data: np.ndarray,
) -> tuple[np.ndarray, MinMaxScaler]:
    """Scale data to [0, 1] range using MinMaxScaler.

    Parameters
    ----------
    data : np.ndarray
        1-D or 2-D array of values.

    Returns
    -------
    scaled_data : np.ndarray
        Data scaled to [0, 1].
    scaler : MinMaxScaler
        Fitted scaler instance (needed to inverse-transform predictions).
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    return scaled_data.flatten(), scaler
