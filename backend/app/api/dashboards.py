"""Dashboards API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Dashboard
from app.models.permission import ResourceType, Permission
from app.schemas import DashboardCreate, DashboardUpdate, DashboardResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("", response_model=List[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all dashboards the current user has access to.

    Returns dashboards where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all dashboards
    result = await db.execute(select(Dashboard))
    all_dashboards = result.scalars().all()

    # Filter dashboards based on permissions
    accessible_dashboards = []
    for dashboard in all_dashboards:
        has_access = await perm_service.check(
            current_user,
            ResourceType.DASHBOARD,
            dashboard.id,
            Permission.READ
        )
        if has_access:
            accessible_dashboards.append(dashboard)

    return accessible_dashboards


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new dashboard.

    Any authenticated user can create a dashboard.
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Create the dashboard
    dashboard = Dashboard(
        name=dashboard_data.name,
        config=dashboard_data.config,
        created_by=current_user.id,
    )

    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.DASHBOARD,
        resource_id=dashboard.id,
    )

    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific dashboard.

    Requires 'read' permission on the dashboard.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.DASHBOARD,
        dashboard_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this dashboard"
        )

    # Get dashboard
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )

    # Convert to response model
    response = DashboardResponse.model_validate(dashboard)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.DASHBOARD,
            dashboard_id
        )

    return response


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    dashboard_update: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a dashboard.

    Requires 'write' permission on the dashboard.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.DASHBOARD,
        dashboard_id,
        Permission.WRITE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this dashboard"
        )

    # Get dashboard
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )

    # Update fields
    if dashboard_update.name is not None:
        dashboard.name = dashboard_update.name
    if dashboard_update.config is not None:
        dashboard.config = dashboard_update.config

    await db.commit()
    await db.refresh(dashboard)

    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a dashboard.

    Requires 'delete' permission on the dashboard.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.DASHBOARD,
        dashboard_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this dashboard"
        )

    # Get dashboard
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )

    # Delete dashboard
    await db.delete(dashboard)
    await db.commit()
