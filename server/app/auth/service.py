import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models.user import User
from app.models.user_session import SessionStatus, UserSession

from .schemas import RegisterRequest, TokenResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ─────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── Token helpers ────────────────────────────────────────────────────────────


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Business logic ───────────────────────────────────────────────────────────


async def register_user(data: RegisterRequest) -> User:
    existing = await User.find_one(User.email == data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
    )
    await user.insert()
    return user


async def authenticate_user(email: str, password: str) -> User | None:
    user = await User.find_one(User.email == email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_session(user: User, access_token: str, refresh_token: str) -> UserSession:
    """Persist a session with hashed tokens so we can validate/revoke later."""
    expire_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    session = UserSession(
        user_id=str(user.id),
        session_token_hash=_hash_token(access_token),
        refresh_token_hash=_hash_token(refresh_token),
        expires_at=expire_at,
    )
    await session.insert()
    return session


async def _issue_tokens(user: User) -> TokenResponse:
    """Issue a fresh access + refresh token pair and persist the session."""
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    await create_session(user, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def login_user(email: str, password: str) -> tuple[User, TokenResponse]:
    user = await authenticate_user(email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update login metadata
    user.last_login_at = datetime.now(timezone.utc)
    user.login_count += 1
    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    tokens = await _issue_tokens(user)
    return user, tokens


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the refresh JWT
    try:
        payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "refresh":
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    # Validate the session exists and is active
    token_hash = _hash_token(refresh_token)
    session = await UserSession.find_one(
        UserSession.refresh_token_hash == token_hash,
        UserSession.status == SessionStatus.ACTIVE,
    )
    if session is None:
        raise credentials_exc

    # Revoke the old session (rotate)
    session.status = SessionStatus.REVOKED
    session.revoked_at = datetime.now(timezone.utc)
    await session.save()

    # Fetch user to include the current role in the new access token
    user = await User.get(user_id)
    if user is None:
        raise credentials_exc

    tokens = await _issue_tokens(user)
    return tokens


async def logout_user(user_id: str) -> None:
    """Revoke all active sessions for the user."""
    sessions = await UserSession.find(
        UserSession.user_id == user_id,
        UserSession.status == SessionStatus.ACTIVE,
    ).to_list()

    now = datetime.now(timezone.utc)
    for session in sessions:
        session.status = SessionStatus.REVOKED
        session.revoked_at = now
        await session.save()
