from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    return {"message": "Registration endpoint - coming soon"}


@router.post("/login")
async def login():
    return {"message": "Login endpoint - coming soon"}


@router.post("/refresh")
async def refresh_token():
    return {"message": "Token refresh endpoint - coming soon"}


@router.get("/me")
async def get_current_user():
    return {"message": "Current user endpoint - coming soon"}
