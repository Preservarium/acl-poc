"""Groups API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Group, User
from app.models.group import group_users
from app.schemas import GroupResponse, UserResponse
from app.core.dependencies import get_current_user

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

    # Add user_count to each group
    response_groups = []
    for group in groups:
        group_dict = {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "user_count": len(group.users) if group.users else 0
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

    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at,
        "user_count": len(group.users) if group.users else 0
    }


@router.get("/{group_id}/members", response_model=list[UserResponse])
async def get_group_members(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all members of a group.
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

    return group.users
