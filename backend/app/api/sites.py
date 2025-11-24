"""Sites API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Site
from app.models.permission import ResourceType, Permission
from app.schemas import SiteCreate, SiteResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/sites", tags=["sites"])


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

    return site


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
