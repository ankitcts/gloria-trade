from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.models.user import AccountStatus, KYCStatus, Permission, UserRole

T = TypeVar("T")


# ── Paginated wrapper ───────────────────────────────────────────────────────


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


# ── User schemas ─────────────────────────────────────────────────────────────


class AdminUserListItem(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    account_status: AccountStatus
    group_ids: list[str]
    created_at: datetime
    last_login_at: Optional[datetime] = None


class AdminUserListResponse(PaginatedResponse[AdminUserListItem]):
    pass


class AdminUserDetailResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str
    preferred_locale: str
    role: UserRole
    account_status: AccountStatus
    extra_permissions: list[Permission]
    group_ids: list[str]
    email_verified: bool
    phone_verified: bool
    kyc_status: KYCStatus
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user) -> "AdminUserDetailResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            preferred_locale=user.preferred_locale,
            role=user.role,
            account_status=user.account_status,
            extra_permissions=user.extra_permissions,
            group_ids=user.group_ids,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            kyc_status=user.kyc.status,
            last_login_at=user.last_login_at,
            login_count=user.login_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER
    account_status: AccountStatus = AccountStatus.ACTIVE
    phone: Optional[str] = None


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class UpdateUserStatusRequest(BaseModel):
    account_status: AccountStatus


class UpdateUserPermissionsRequest(BaseModel):
    extra_permissions: list[Permission]


class UpdateUserGroupsRequest(BaseModel):
    group_ids: list[str]


# ── Group schemas ────────────────────────────────────────────────────────────


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    permissions: list[Permission] = Field(default_factory=list)


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    permissions: Optional[list[Permission]] = None


class AddGroupMembersRequest(BaseModel):
    user_ids: list[str]


class RemoveGroupMembersRequest(BaseModel):
    user_ids: list[str]


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: list[Permission]
    member_ids: list[str]
    member_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_group(cls, group) -> "GroupResponse":
        return cls(
            id=str(group.id),
            name=group.name,
            description=group.description,
            permissions=group.permissions,
            member_ids=group.member_ids,
            member_count=len(group.member_ids),
            created_by=group.created_by,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )
