from fastapi import APIRouter

router = APIRouter()


@router.get("/{code}/historic-signals")
async def get_historic_signals(code: str):
    return {"message": f"Historic signals for {code} - coming soon"}


@router.post("/{code}/simulate")
async def simulate_trading(code: str):
    return {"message": f"Simulate trading for {code} - coming soon"}
