import logging
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)


class LSTMPricePredictor(nn.Module):
    """Two-layer LSTM for univariate price prediction.

    Architecture:
        LSTM(input_size, 50, num_layers=2, dropout=0.2, batch_first=True)
        Linear(50, 25) + ReLU
        Linear(25, 1)
    """

    def __init__(self, input_size: int = 1, hidden_size: int = 50, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.fc1 = nn.Linear(hidden_size, 25)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(25, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Take the output from the last time-step
        last_hidden = lstm_out[:, -1, :]  # (batch, hidden_size)
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.fc2(out)
        return out.squeeze(-1)  # (batch,)


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    epochs: int = 10,
    batch_size: int = 32,
    lr: float = 0.001,
    device: Optional[str] = None,
) -> tuple["LSTMPricePredictor", list[float]]:
    """Train an LSTMPricePredictor on the given data.

    Parameters
    ----------
    X_train : np.ndarray of shape (samples, lookback_window, 1)
    y_train : np.ndarray of shape (samples,)
    epochs : int
    batch_size : int
    lr : float
    device : str, optional
        Force a device ('cpu', 'cuda', 'mps'). Auto-detected if None.

    Returns
    -------
    model : LSTMPricePredictor (on CPU, in eval mode)
    loss_history : list[float]  per-epoch average loss
    """
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    logger.info("Training LSTM on device=%s  epochs=%d  batch_size=%d  lr=%s", device, epochs, batch_size, lr)

    input_size = X_train.shape[2] if X_train.ndim == 3 else 1
    model = LSTMPricePredictor(input_size=input_size).to(device)

    X_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_tensor = torch.tensor(y_train, dtype=torch.float32)

    dataset = TensorDataset(X_tensor, y_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    loss_history: list[float] = []

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        batches = 0
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()
            predictions = model(X_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batches += 1

        avg_loss = epoch_loss / max(batches, 1)
        loss_history.append(avg_loss)
        logger.info("Epoch %d/%d  loss=%.6f", epoch + 1, epochs, avg_loss)

    # Move back to CPU for serialisation
    model = model.cpu()
    model.eval()
    return model, loss_history


def predict(
    model: LSTMPricePredictor,
    X_test: np.ndarray,
    scaler: MinMaxScaler,
) -> np.ndarray:
    """Generate predictions and inverse-transform them to the original scale.

    Parameters
    ----------
    model : LSTMPricePredictor (CPU, eval mode)
    X_test : np.ndarray of shape (samples, lookback_window, 1)
    scaler : MinMaxScaler fitted on the training close prices

    Returns
    -------
    predictions : np.ndarray of shape (samples,) in original price scale
    """
    model.eval()
    with torch.no_grad():
        X_tensor = torch.tensor(X_test, dtype=torch.float32)
        preds_scaled = model(X_tensor).numpy()

    # Inverse-transform: scaler expects 2-D
    preds_original = scaler.inverse_transform(preds_scaled.reshape(-1, 1)).flatten()
    return preds_original
