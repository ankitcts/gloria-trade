from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_permission
from app.models.user import AccountStatus, Permission, User, UserRole

from . import service
from .schemas import (
    AddGroupMembersRequest,
    AdminUserDetailResponse,
    AdminUserListItem,
    AdminUserListResponse,
    CreateGroupRequest,
    CreateUserRequest,
    GroupResponse,
    RemoveGroupMembersRequest,
    UpdateGroupRequest,
    UpdateUserGroupsRequest,
    UpdateUserPermissionsRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
)

router = APIRouter()

AdminUser = Annotated[User, Depends(require_permission(Permission.ADMIN_USERS))]


# ── Permissions reference ────────────────────────────────────────────────────


@router.get("/permissions", response_model=list[str])
async def list_permissions(_current_user: AdminUser):
    """Return all available permission values."""
    return [p.value for p in Permission]


# ── Group endpoints (registered before /{user_id} to avoid route conflicts) ─


@router.get("/groups", response_model=list[GroupResponse])
async def list_groups(_current_user: AdminUser):
    """List all groups."""
    groups = await service.list_groups()
    return [GroupResponse.from_group(g) for g in groups]


@router.post("/groups", response_model=GroupResponse, status_code=201)
async def create_group(body: CreateGroupRequest, current_user: AdminUser):
    """Create a new group."""
    group = await service.create_group(
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        created_by=str(current_user.id),
    )
    return GroupResponse.from_group(group)


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str, _current_user: AdminUser):
    """Get a group by ID."""
    group = await service.get_group(group_id)
    return GroupResponse.from_group(group)


@router.patch("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str, body: UpdateGroupRequest, _current_user: AdminUser
):
    """Update group details."""
    group = await service.update_group(
        group_id=group_id,
        name=body.name,
        description=body.description,
        permissions=body.permissions,
    )
    return GroupResponse.from_group(group)


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(group_id: str, _current_user: AdminUser):
    """Delete a group and remove it from all users."""
    await service.delete_group(group_id)


@router.post("/groups/{group_id}/members", response_model=GroupResponse)
async def add_group_members(
    group_id: str, body: AddGroupMembersRequest, _current_user: AdminUser
):
    """Add users to a group."""
    group = await service.add_group_members(group_id, body.user_ids)
    return GroupResponse.from_group(group)


@router.delete("/groups/{group_id}/members", response_model=GroupResponse)
async def remove_group_members(
    group_id: str, body: RemoveGroupMembersRequest, _current_user: AdminUser
):
    """Remove users from a group."""
    group = await service.remove_group_members(group_id, body.user_ids)
    return GroupResponse.from_group(group)


# ── User endpoints ──────────────────────────────────────────────────────────


@router.post("/", response_model=AdminUserDetailResponse, status_code=201)
async def create_user(body: CreateUserRequest, _current_user: AdminUser):
    """Create a new user (admin only)."""
    user = await service.create_user(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        account_status=body.account_status,
        phone=body.phone,
    )
    return AdminUserDetailResponse.from_user(user)


@router.get("/", response_model=AdminUserListResponse)
async def list_users(
    _current_user: AdminUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[AccountStatus] = None,
    search: Optional[str] = None,
):
    """List all users with optional filters and pagination."""
    users, total = await service.list_users(
        page=page,
        page_size=page_size,
        role_filter=role,
        status_filter=status,
        search=search,
    )
    items = [
        AdminUserListItem(
            id=str(u.id),
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            account_status=u.account_status,
            group_ids=u.group_ids,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
        )
        for u in users
    ]
    return AdminUserListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{user_id}", response_model=AdminUserDetailResponse)
async def get_user(user_id: str, _current_user: AdminUser):
    """Get full details for a single user."""
    user = await service.get_user_detail(user_id)
    return AdminUserDetailResponse.from_user(user)


@router.patch("/{user_id}/role", response_model=AdminUserDetailResponse)
async def update_user_role(
    user_id: str, body: UpdateUserRoleRequest, _current_user: AdminUser
):
    """Change a user's role."""
    user = await service.update_user_role(user_id, body.role)
    return AdminUserDetailResponse.from_user(user)


@router.patch("/{user_id}/status", response_model=AdminUserDetailResponse)
async def update_user_status(
    user_id: str, body: UpdateUserStatusRequest, _current_user: AdminUser
):
    """Activate, suspend, or deactivate a user."""
    user = await service.update_user_status(user_id, body.account_status)
    return AdminUserDetailResponse.from_user(user)


@router.patch("/{user_id}/permissions", response_model=AdminUserDetailResponse)
async def update_user_permissions(
    user_id: str, body: UpdateUserPermissionsRequest, _current_user: AdminUser
):
    """Set a user's extra permissions."""
    user = await service.update_user_permissions(user_id, body.extra_permissions)
    return AdminUserDetailResponse.from_user(user)


@router.patch("/{user_id}/groups", response_model=AdminUserDetailResponse)
async def update_user_groups(
    user_id: str, body: UpdateUserGroupsRequest, _current_user: AdminUser
):
    """Set a user's group memberships."""
    user = await service.update_user_groups(user_id, body.group_ids)
    return AdminUserDetailResponse.from_user(user)


@router.delete("/{user_id}", response_model=AdminUserDetailResponse)
async def delete_user(user_id: str, _current_user: AdminUser):
    """Soft-delete a user (set status to deactivated)."""
    user = await service.delete_user(user_id)
    return AdminUserDetailResponse.from_user(user)
