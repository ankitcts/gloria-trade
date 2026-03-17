from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.auth.service import hash_password
from app.models.group import UserGroup
from app.models.user import AccountStatus, Permission, User, UserRole


# ── User management ─────────────────────────────────────────────────────────


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole = UserRole.VIEWER,
    account_status: AccountStatus = AccountStatus.ACTIVE,
    phone: str | None = None,
) -> User:
    """Create a new user as admin (no self-registration flow)."""
    existing = await User.find_one(User.email == email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        account_status=account_status,
        created_at=now,
        updated_at=now,
    )
    await user.insert()
    return user


async def list_users(
    page: int = 1,
    page_size: int = 20,
    role_filter: Optional[UserRole] = None,
    status_filter: Optional[AccountStatus] = None,
    search: Optional[str] = None,
) -> tuple[list[User], int]:
    """Return a paginated list of users with optional filters."""
    query: dict = {}

    if role_filter is not None:
        query["role"] = role_filter.value
    if status_filter is not None:
        query["account_status"] = status_filter.value
    if search:
        query["$text"] = {"$search": search}

    total = await User.find(query).count()
    skip = (page - 1) * page_size
    users = await User.find(query).skip(skip).limit(page_size).sort("-created_at").to_list()
    return users, total


async def get_user_detail(user_id: str) -> User:
    """Get a single user by ID or raise 404."""
    user = await User.get(PydanticObjectId(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


async def update_user_role(user_id: str, role: UserRole) -> User:
    """Change a user's role."""
    user = await get_user_detail(user_id)
    user.role = role
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return user


async def update_user_status(user_id: str, account_status: AccountStatus) -> User:
    """Activate, suspend, or deactivate a user."""
    user = await get_user_detail(user_id)
    user.account_status = account_status
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return user


async def update_user_permissions(user_id: str, permissions: list[Permission]) -> User:
    """Set a user's extra permissions."""
    user = await get_user_detail(user_id)
    user.extra_permissions = permissions
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return user


async def update_user_groups(user_id: str, group_ids: list[str]) -> User:
    """Set a user's group memberships, keeping both sides in sync."""
    user = await get_user_detail(user_id)
    old_group_ids = set(user.group_ids)
    new_group_ids = set(group_ids)

    # Validate that all target groups exist
    if new_group_ids:
        oids = [PydanticObjectId(gid) for gid in new_group_ids]
        existing = await UserGroup.find({"_id": {"$in": oids}}).to_list()
        existing_ids = {str(g.id) for g in existing}
        missing = new_group_ids - existing_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Groups not found: {', '.join(missing)}",
            )

    uid = str(user.id)

    # Remove user from groups they are no longer in
    removed = old_group_ids - new_group_ids
    for gid in removed:
        group = await UserGroup.get(PydanticObjectId(gid))
        if group and uid in group.member_ids:
            group.member_ids.remove(uid)
            group.updated_at = datetime.now(timezone.utc)
            await group.save()

    # Add user to new groups
    added = new_group_ids - old_group_ids
    for gid in added:
        group = await UserGroup.get(PydanticObjectId(gid))
        if group and uid not in group.member_ids:
            group.member_ids.append(uid)
            group.updated_at = datetime.now(timezone.utc)
            await group.save()

    user.group_ids = list(new_group_ids)
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return user


async def delete_user(user_id: str) -> User:
    """Soft-delete a user by setting status to deactivated."""
    user = await get_user_detail(user_id)
    user.account_status = AccountStatus.DEACTIVATED
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    return user


# ── Group management ────────────────────────────────────────────────────────


async def list_groups() -> list[UserGroup]:
    """Return all groups."""
    return await UserGroup.find_all().sort("-created_at").to_list()


async def create_group(
    name: str,
    description: Optional[str],
    permissions: list[Permission],
    created_by: str,
) -> UserGroup:
    """Create a new user group."""
    existing = await UserGroup.find_one(UserGroup.name == name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A group with this name already exists.",
        )

    now = datetime.now(timezone.utc)
    group = UserGroup(
        name=name,
        description=description,
        permissions=permissions,
        member_ids=[],
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    await group.insert()
    return group


async def get_group(group_id: str) -> UserGroup:
    """Get a group by ID or raise 404."""
    group = await UserGroup.get(PydanticObjectId(group_id))
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found.",
        )
    return group


async def update_group(
    group_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permissions: Optional[list[Permission]] = None,
) -> UserGroup:
    """Update group details."""
    group = await get_group(group_id)

    if name is not None and name != group.name:
        existing = await UserGroup.find_one(UserGroup.name == name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A group with this name already exists.",
            )
        group.name = name

    if description is not None:
        group.description = description

    if permissions is not None:
        group.permissions = permissions

    group.updated_at = datetime.now(timezone.utc)
    await group.save()
    return group


async def delete_group(group_id: str) -> None:
    """Delete a group and remove it from all users' group_ids."""
    group = await get_group(group_id)
    gid = str(group.id)

    # Remove group from all users that reference it
    users = await User.find({"group_ids": gid}).to_list()
    for user in users:
        user.group_ids.remove(gid)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

    await group.delete()


async def add_group_members(group_id: str, user_ids: list[str]) -> UserGroup:
    """Add users to a group, updating both sides."""
    group = await get_group(group_id)
    gid = str(group.id)

    for uid in user_ids:
        user = await User.get(PydanticObjectId(uid))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {uid}",
            )

        if uid not in group.member_ids:
            group.member_ids.append(uid)

        if gid not in user.group_ids:
            user.group_ids.append(gid)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()

    group.updated_at = datetime.now(timezone.utc)
    await group.save()
    return group


async def remove_group_members(group_id: str, user_ids: list[str]) -> UserGroup:
    """Remove users from a group, updating both sides."""
    group = await get_group(group_id)
    gid = str(group.id)

    for uid in user_ids:
        user = await User.get(PydanticObjectId(uid))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {uid}",
            )

        if uid in group.member_ids:
            group.member_ids.remove(uid)

        if gid in user.group_ids:
            user.group_ids.remove(gid)
            user.updated_at = datetime.now(timezone.utc)
            await user.save()

    group.updated_at = datetime.now(timezone.utc)
    await group.save()
    return group
