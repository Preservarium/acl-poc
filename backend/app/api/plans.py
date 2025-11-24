"""Plans API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Plan, Site
from app.models.permission import ResourceType, Permission
from app.schemas import PlanCreate, PlanResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all plans the current user has access to.

    Returns plans where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all plans
    result = await db.execute(select(Plan))
    all_plans = result.scalars().all()

    # Filter plans based on permissions
    accessible_plans = []
    for plan in all_plans:
        has_access = await perm_service.check(
            current_user,
            ResourceType.PLAN,
            plan.id,
            Permission.READ
        )
        if has_access:
            accessible_plans.append(plan)

    return accessible_plans


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new plan.

    Requires 'create' permission on the parent site.
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Check if site exists
    result = await db.execute(select(Site).where(Site.id == plan_data.site_id))
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Check 'create' permission on parent site
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SITE,
        plan_data.site_id,
        Permission.CREATE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create plans in this site"
        )

    # Create the plan
    plan = Plan(
        name=plan_data.name,
        site_id=plan_data.site_id,
        created_by=current_user.id,
    )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.PLAN,
        resource_id=plan.id,
    )

    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific plan.

    Requires 'read' permission on the plan.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.PLAN,
        plan_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this plan"
        )

    # Get plan
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a plan.

    Requires 'delete' permission on the plan.
    Cascades to all sensors within the plan.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.PLAN,
        plan_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this plan"
        )

    # Get plan
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    # Delete plan (cascades to sensors)
    await db.delete(plan)
    await db.commit()
