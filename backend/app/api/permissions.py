"""Permissions API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.database import get_db
from app.models import User, Group, Site, Plan, Sensor, ResourcePermission
from app.models.permission import ResourceType, Permission as PermissionEnum
from app.schemas import (
    PermissionCreate,
    PermissionResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCheckResult,
)
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/permissions", tags=["permissions"])


async def get_grantee_name(db: AsyncSession, grantee_type: str, grantee_id: str) -> Optional[str]:
    """Get the name of a grantee (user or group)."""
    if grantee_type == "user":
        result = await db.execute(select(User).where(User.id == grantee_id))
        user = result.scalar_one_or_none()
        return user.username if user else None
    elif grantee_type == "group":
        result = await db.execute(select(Group).where(Group.id == grantee_id))
        group = result.scalar_one_or_none()
        return group.name if group else None
    return None


async def get_resource_name(db: AsyncSession, resource_type: str, resource_id: str) -> Optional[str]:
    """Get the name of a resource."""
    if resource_type == "site":
        result = await db.execute(select(Site).where(Site.id == resource_id))
        site = result.scalar_one_or_none()
        return site.name if site else None
    elif resource_type == "plan":
        result = await db.execute(select(Plan).where(Plan.id == resource_id))
        plan = result.scalar_one_or_none()
        return plan.name if plan else None
    elif resource_type == "sensor":
        result = await db.execute(select(Sensor).where(Sensor.id == resource_id))
        sensor = result.scalar_one_or_none()
        return sensor.name if sensor else None
    return None


async def enrich_permission(db: AsyncSession, perm: ResourcePermission) -> PermissionResponse:
    """Enrich a permission with grantee and resource names."""
    grantee_name = await get_grantee_name(db, perm.grantee_type.value, perm.grantee_id)
    resource_name = await get_resource_name(db, perm.resource_type.value, perm.resource_id)

    return PermissionResponse(
        id=perm.id,
        grantee_type=perm.grantee_type,
        grantee_id=perm.grantee_id,
        grantee_name=grantee_name,
        resource_type=perm.resource_type,
        resource_id=perm.resource_id,
        resource_name=resource_name,
        permission=perm.permission,
        effect=perm.effect,
        inherit=perm.inherit,
        granted_by=perm.granted_by,
        granted_at=perm.granted_at,
    )


@router.get("", response_model=List[PermissionResponse])
async def list_my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all permissions granted to the current user (directly or through groups).
    """
    perm_service = PermissionService(db)

    # Get user's permissions
    user_perms = await perm_service.list_for_user(current_user.id)

    # Get group permissions
    group_ids = [group.id for group in current_user.groups]
    group_perms = []
    if group_ids:
        result = await db.execute(
            select(ResourcePermission).where(
                and_(
                    ResourcePermission.grantee_type == "group",
                    ResourcePermission.grantee_id.in_(group_ids)
                )
            )
        )
        group_perms = result.scalars().all()

    all_perms = list(user_perms) + list(group_perms)

    # Enrich with names
    enriched = []
    for perm in all_perms:
        enriched.append(await enrich_permission(db, perm))

    return enriched


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[PermissionResponse])
async def list_resource_permissions(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all permissions for a specific resource.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Check if user has manage permission on the resource
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}"
        )

    has_permission = await perm_service.check(
        current_user,
        rt,
        resource_id,
        PermissionEnum.MANAGE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view permissions for this resource"
        )

    # Get permissions
    permissions = await perm_service.list_for_resource(rt, resource_id)

    # Enrich with names
    enriched = []
    for perm in permissions:
        enriched.append(await enrich_permission(db, perm))

    return enriched


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_permission(
    perm_create: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Grant a permission to a user or group.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Check if current user has manage permission on the resource
    has_permission = await perm_service.check(
        current_user,
        perm_create.resource_type,
        perm_create.resource_id,
        PermissionEnum.MANAGE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to grant permissions on this resource"
        )

    # Verify grantee exists
    if perm_create.grantee_type.value == "user":
        result = await db.execute(select(User).where(User.id == perm_create.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    elif perm_create.grantee_type.value == "group":
        result = await db.execute(select(Group).where(Group.id == perm_create.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )

    # Grant permission
    permission = await perm_service.grant(
        grantee_type=perm_create.grantee_type,
        grantee_id=perm_create.grantee_id,
        resource_type=perm_create.resource_type,
        resource_id=perm_create.resource_id,
        permission=perm_create.permission,
        effect=perm_create.effect,
        inherit=perm_create.inherit,
        granted_by=current_user.id,
    )

    # Enrich and return
    return await enrich_permission(db, permission)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke a permission.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Get the permission to check
    result = await db.execute(
        select(ResourcePermission).where(ResourcePermission.id == permission_id)
    )
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # Check if current user has manage permission on the resource
    has_permission = await perm_service.check(
        current_user,
        permission.resource_type,
        permission.resource_id,
        PermissionEnum.MANAGE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to revoke permissions on this resource"
        )

    # Revoke
    success = await perm_service.revoke(permission_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permissions(
    check_request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk check permissions for the current user.
    """
    perm_service = PermissionService(db)

    results = []
    for check in check_request.checks:
        allowed = await perm_service.check(
            current_user,
            check.resource_type,
            check.resource_id,
            check.permission
        )

        results.append(
            PermissionCheckResult(
                resource_type=check.resource_type,
                resource_id=check.resource_id,
                permission=check.permission,
                allowed=allowed,
            )
        )

    return PermissionCheckResponse(results=results)
