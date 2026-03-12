from fastapi import APIRouter

router = APIRouter()


@router.get("/settings")
async def get_portfolio_settings():
    return {"message": "Portfolio settings - coming soon"}


@router.put("/settings")
async def update_portfolio_settings():
    return {"message": "Update portfolio settings - coming soon"}


@router.get("/summary")
async def get_portfolio_summary(period: str = "yearly"):
    return {"message": f"Portfolio summary ({period}) - coming soon"}
