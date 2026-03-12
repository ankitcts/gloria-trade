from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.models.user import Permission, ROLE_PERMISSIONS, User, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    """Extract and validate the JWT from the Authorization header and return the User."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    user = await User.get(user_id)
    if user is None:
        raise credentials_exc

    return user


def require_role(required_role: UserRole):
    """Return a dependency that ensures the current user has the specified role."""

    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' is required.",
            )
        return current_user

    return _check_role


def require_permission(required_permission: Permission):
    """Return a dependency that ensures the current user holds the specified permission."""

    async def _check_permission(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        # Collect role-based permissions plus any extra user-level grants
        user_permissions = set(ROLE_PERMISSIONS.get(current_user.role, []))
        user_permissions.update(current_user.extra_permissions)

        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission.value}' is required.",
            )
        return current_user

    return _check_permission
