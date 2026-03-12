from fastapi import APIRouter

router = APIRouter()


@router.get("/{symbol}")
async def get_predictions(symbol: str):
    return {"message": f"Predictions for {symbol} - coming soon"}


@router.post("/{symbol}/train")
async def train_model(symbol: str):
    return {"message": f"Train model for {symbol} - coming soon"}


@router.get("/{symbol}/actual")
async def get_actual_data(symbol: str):
    return {"message": f"Actual data for {symbol} - coming soon"}
