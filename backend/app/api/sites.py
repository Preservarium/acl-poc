"""Sites API endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import User, Site, ResourcePermission, Group
from app.models.permission import ResourceType, Permission, GranteeType
from app.schemas import SiteCreate, SiteResponse, UserResponse
from app.schemas.permission import PermissionWithGrantee
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/sites", tags=["sites"])


def parse_fields(fields):
    """Parse fields from database - handle both list and JSON string."""
    if fields is None:
        return None
    if isinstance(fields, list):
        return fields
    if isinstance(fields, str):
        try:
            return json.loads(fields)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


@router.get("", response_model=List[SiteResponse])
async def list_sites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all sites the current user has access to.

    Returns sites where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all sites
    result = await db.execute(select(Site))
    all_sites = result.scalars().all()

    # Filter sites based on permissions
    accessible_sites = []
    for site in all_sites:
        has_access = await perm_service.check(
            current_user,
            ResourceType.SITE,
            site.id,
            Permission.READ
        )
        if has_access:
            accessible_sites.append(site)

    return accessible_sites


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new site.

    Only admins can create sites (root resources).
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Create the site
    site = Site(
        name=site_data.name,
        created_by=current_user.id,
    )

    db.add(site)
    await db.commit()
    await db.refresh(site)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.SITE,
        resource_id=site.id,
    )

    return site


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific site.

    Requires 'read' permission on the site.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SITE,
        site_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this site"
        )

    # Get site
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Convert to response model
    response = SiteResponse.model_validate(site)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.SITE,
            site_id
        )

    return response


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a site.

    Requires 'delete' permission on the site.
    Cascades to all plans and sensors within the site.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SITE,
        site_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this site"
        )

    # Get site
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Delete site (cascades to plans and sensors)
    await db.delete(site)
    await db.commit()


@router.get("/{site_id}/admins", response_model=List[UserResponse])
async def get_site_admins(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all users with 'manage' permission on a site (site admins).

    Requires 'read' permission on the site.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SITE,
        site_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this site"
        )

    # Check if site exists
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Get all users with 'manage' permission on this site
    result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.resource_type == ResourceType.SITE,
                ResourcePermission.resource_id == site_id,
                ResourcePermission.permission == Permission.MANAGE,
                ResourcePermission.grantee_type == GranteeType.USER
            )
        )
    )
    permissions = result.scalars().all()

    # Get unique user IDs
    user_ids = list(set([perm.grantee_id for perm in permissions]))

    # Get users
    if not user_ids:
        return []

    result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users = result.scalars().all()

    return users


@router.get("/{site_id}/permissions", response_model=List[PermissionWithGrantee])
async def get_site_permissions(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all permissions on this site.

    Returns list of permissions with grantee details.
    For group grantees, includes member list.

    Requires 'read' permission on the site.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SITE,
        site_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this site"
        )

    # Check if site exists
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Get all permissions for this site
    result = await db.execute(
        select(ResourcePermission).where(
            and_(
                ResourcePermission.resource_type == ResourceType.SITE,
                ResourcePermission.resource_id == site_id
            )
        )
    )
    permissions = result.scalars().all()

    # Build response with grantee details
    response_permissions = []

    for perm in permissions:
        # Get grantee name
        grantee_name = None
        members = None
        member_count = None

        if perm.grantee_type == GranteeType.USER:
            user_result = await db.execute(
                select(User).where(User.id == perm.grantee_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                grantee_name = user.username
        elif perm.grantee_type == GranteeType.GROUP:
            group_result = await db.execute(
                select(Group).where(Group.id == perm.grantee_id)
            )
            group = group_result.scalar_one_or_none()
            if group:
                grantee_name = group.name
                # Get group members
                group_members = await group.get_members(db)
                member_count = len(group_members)
                members = [member.username for member in group_members]

        # Get granter name
        granted_by_name = None
        if perm.granted_by:
            granter_result = await db.execute(
                select(User).where(User.id == perm.granted_by)
            )
            granter = granter_result.scalar_one_or_none()
            if granter:
                granted_by_name = granter.username

        response_permissions.append(
            PermissionWithGrantee(
                id=perm.id,
                grantee_type=perm.grantee_type,
                grantee_id=perm.grantee_id,
                grantee_name=grantee_name or perm.grantee_id,
                permission=perm.permission,
                effect=perm.effect,
                inherit=perm.inherit,
                fields=parse_fields(perm.fields),
                expires_at=perm.expires_at,
                granted_at=perm.granted_at,
                granted_by_name=granted_by_name,
                members=members,
                member_count=member_count
            )
        )

    return response_permissions
