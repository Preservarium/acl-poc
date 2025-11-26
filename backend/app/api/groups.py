"""Groups API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime

from app.database import get_db
from app.models import Group, User, ResourcePermission
from app.models.permission import (
    Permission as PermissionEnum,
    GranteeType,
    ResourceType,
    Effect
)
from app.schemas import GroupResponse, UserResponse, PermissionResponse
from app.core.dependencies import get_current_user
from app.api.permissions import enrich_permission

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of all groups.

    Returns list of groups with member counts.
    """
    result = await db.execute(
        select(Group).order_by(Group.name)
    )
    groups = result.scalars().all()

    # Add user_count to each group by querying member permissions
    response_groups = []
    for group in groups:
        # Count members via resource_permissions
        member_count_result = await db.execute(
            select(func.count(ResourcePermission.id))
            .where(
                and_(
                    ResourcePermission.grantee_type == GranteeType.USER,
                    ResourcePermission.resource_type == ResourceType.GROUP,
                    ResourcePermission.resource_id == group.id,
                    ResourcePermission.permission == PermissionEnum.MEMBER,
                    ResourcePermission.effect == Effect.ALLOW,
                    or_(
                        ResourcePermission.expires_at.is_(None),
                        ResourcePermission.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        user_count = member_count_result.scalar() or 0

        group_dict = {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "user_count": user_count
        }
        response_groups.append(group_dict)

    return response_groups


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific group by ID.
    """
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Count members via resource_permissions
    member_count_result = await db.execute(
        select(func.count(ResourcePermission.id))
        .where(
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.resource_type == ResourceType.GROUP,
                ResourcePermission.resource_id == group.id,
                ResourcePermission.permission == PermissionEnum.MEMBER,
                ResourcePermission.effect == Effect.ALLOW,
                or_(
                    ResourcePermission.expires_at.is_(None),
                    ResourcePermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    user_count = member_count_result.scalar() or 0

    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at,
        "user_count": user_count
    }


@router.get("/{group_id}/members", response_model=list[UserResponse])
async def get_group_members(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all members of a group.

    Returns users who have 'member' permission on this group.
    """
    # Check if group exists
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Get user IDs with member permission
    member_perms_result = await db.execute(
        select(ResourcePermission.grantee_id)
        .where(
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.resource_type == ResourceType.GROUP,
                ResourcePermission.resource_id == group_id,
                ResourcePermission.permission == PermissionEnum.MEMBER,
                ResourcePermission.effect == Effect.ALLOW,
                or_(
                    ResourcePermission.expires_at.is_(None),
                    ResourcePermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    user_ids = [row[0] for row in member_perms_result.all()]

    # Get user objects
    if not user_ids:
        return []

    users_result = await db.execute(
        select(User).where(User.id.in_(user_ids)).order_by(User.username)
    )
    users = users_result.scalars().all()

    return users


@router.post("/{group_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a user to a group.

    Creates a 'member' permission for the user on this group.
    """
    # Check if group exists
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Check if user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if membership already exists
    existing_result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.grantee_id == user_id,
                ResourcePermission.resource_type == ResourceType.GROUP,
                ResourcePermission.resource_id == group_id,
                ResourcePermission.permission == PermissionEnum.MEMBER
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group"
        )

    # Create member permission
    member_permission = ResourcePermission(
        grantee_type=GranteeType.USER,
        grantee_id=user_id,
        resource_type=ResourceType.GROUP,
        resource_id=group_id,
        permission=PermissionEnum.MEMBER,
        effect=Effect.ALLOW,
        inherit=False,
        fields=None,
        granted_by=current_user.id
    )
    db.add(member_permission)
    await db.commit()

    return {"message": "User added to group successfully"}


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a user from a group.

    Deletes the 'member' permission for the user on this group.
    """
    # Check if group exists
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Find and delete member permission
    perm_result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.grantee_id == user_id,
                ResourcePermission.resource_type == ResourceType.GROUP,
                ResourcePermission.resource_id == group_id,
                ResourcePermission.permission == PermissionEnum.MEMBER
            )
        )
    )
    permission = perm_result.scalar_one_or_none()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group"
        )

    await db.delete(permission)
    await db.commit()

    return None


@router.get("/{group_id}/permissions", response_model=List[PermissionResponse])
async def get_group_permissions(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all permissions granted to a group.

    Returns all resource permissions where the group is the grantee.
    """
    # Check if group exists
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Get all permissions for the group
    result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.grantee_type == "group",
                ResourcePermission.grantee_id == group_id
            )
        )
    )
    permissions = result.scalars().all()

    # Enrich with names
    enriched = []
    for perm in permissions:
        enriched.append(await enrich_permission(db, perm))

    return enriched
