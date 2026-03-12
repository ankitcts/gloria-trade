from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.models.user import User

from .dependencies import get_current_user
from .schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from .service import login_user, logout_user, refresh_access_token, register_user, _issue_tokens

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest) -> TokenResponse:
    """Create a new user account and return authentication tokens."""
    user = await register_user(data)
    tokens = await _issue_tokens(user)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest) -> TokenResponse:
    """Authenticate with email and password and return tokens."""
    _user, tokens = await login_user(data.email, data.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    return await refresh_access_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.from_user(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: Annotated[User, Depends(get_current_user)]) -> None:
    """Revoke all active sessions for the current user."""
    await logout_user(str(current_user.id))
