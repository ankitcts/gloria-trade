from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_securities():
    return {"message": "List securities endpoint - coming soon"}


@router.get("/search")
async def search_securities(q: str = ""):
    return {"message": f"Search securities for '{q}' - coming soon"}


@router.get("/{code}/history")
async def get_security_history(code: str):
    return {"message": f"History for {code} - coming soon"}


@router.post("/{code}/analyze")
async def analyze_security(code: str):
    return {"message": f"Analyze {code} - coming soon"}


@router.get("/{code}/analysis")
async def get_security_analysis(code: str):
    return {"message": f"Analysis for {code} - coming soon"}
