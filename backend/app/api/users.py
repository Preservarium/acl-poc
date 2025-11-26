"""Users API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.models.permission import ResourceType, Permission, ResourcePermission
from app.schemas import (
    UserResponse,
    UserUpdate,
    UserAdminUpdate,
    PermissionCreate,
    PermissionResponse,
    EffectivePermissionsResponse,
    UserBasic,
    GroupBasic,
    ResourceWithSource,
    DirectPermission
)
from app.core.dependencies import get_current_user
from app.core.business_rules import validate_self_update
from app.core.security import get_password_hash
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of all users.

    Returns list of users (excluding password hashes).
    """
    result = await db.execute(
        select(User).order_by(User.username)
    )
    users = result.scalars().all()

    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific user by ID.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a user's information.

    This endpoint enforces:
    1. Self-update business rules (non-admins can't modify username, is_admin, disabled on themselves)
    2. ACL permissions (users need 'write' permission to modify other users)
    3. Field-level restrictions (if ACL specifies field constraints)

    Args:
        user_id: ID of the user to update
        updates: Fields to update (UserAdminUpdate allows all fields)
        db: Database session
        current_user: The authenticated user making the request

    Returns:
        Updated user information

    Raises:
        HTTPException 404: User not found
        HTTPException 403: Permission denied or self-update rule violation
    """
    # Get the target user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Convert updates to dict, excluding None values
    update_data = updates.model_dump(exclude_unset=True)

    if not update_data:
        # No updates provided, return current user
        return target_user

    # Check if this is a self-update
    is_self_update = current_user.id == user_id

    if is_self_update:
        # Apply self-update business rules
        # Admins bypass these rules - they can modify any field on themselves
        validate_self_update(update_data, is_admin=current_user.is_admin)
    else:
        # This is updating another user - check ACL permissions
        permission_service = PermissionService(db)

        # Check if current user has permission to modify target user
        # This requires 'write' permission on the user resource
        allowed, fields = await permission_service.check(
            current_user,
            ResourceType.USER,
            user_id,
            Permission.WRITE
        )

        if not allowed and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this user"
            )

        # If fields are restricted, validate updates
        if fields is not None:
            for field in update_data.keys():
                if field not in fields:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You don't have permission to modify field '{field}'"
                    )

    # Hash password if it's being updated
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))

    # Apply updates to target user
    for field, value in update_data.items():
        if hasattr(target_user, field):
            setattr(target_user, field, value)

    # Save changes
    await db.commit()
    await db.refresh(target_user)

    return target_user


@router.get("/{user_id}/permissions", response_model=List[PermissionResponse])
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get permissions granted ON this user (who can manage this user).

    Only admins or users with 'manage' permission on this user can view.
    """
    perm_service = PermissionService(db)

    # Verify target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if current user can read this user's permissions
    # Admins can always read, or if you have manage permission on the user
    if not current_user.is_admin:
        has_permission, _ = await perm_service.check(
            current_user,
            ResourceType.USER,
            user_id,
            Permission.MANAGE
        )

        if not has_permission and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this user's permissions"
            )

    # Get permissions where resource_type='user' and resource_id=user_id
    permissions = await perm_service.list_for_resource(ResourceType.USER, user_id)

    # Enrich with names
    from app.api.permissions import enrich_permission
    enriched = []
    for perm in permissions:
        enriched.append(await enrich_permission(db, perm))

    return enriched


@router.post("/{user_id}/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_user_permission(
    user_id: str,
    permission: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Grant permission on this user to another user/group.

    Only admins or users with 'manage' on this user can grant.
    """
    perm_service = PermissionService(db)

    # Verify target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Override resource_type and resource_id to ensure they're set to this user
    permission.resource_type = ResourceType.USER
    permission.resource_id = user_id

    # Check if current user has manage permission on this user
    if not current_user.is_admin:
        has_permission, _ = await perm_service.check(
            current_user,
            ResourceType.USER,
            user_id,
            Permission.MANAGE
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to grant permissions on this user"
            )

    # Verify grantee exists (reuse logic from permissions.py)
    from app.models import Group

    if permission.grantee_type.value == "user":
        result = await db.execute(select(User).where(User.id == permission.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grantee user not found"
            )
    elif permission.grantee_type.value == "group":
        result = await db.execute(select(Group).where(Group.id == permission.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grantee group not found"
            )

    # Grant permission
    perm = await perm_service.grant(
        grantee_type=permission.grantee_type,
        grantee_id=permission.grantee_id,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        permission=permission.permission,
        effect=permission.effect,
        inherit=permission.inherit,
        granted_by=current_user.id,
    )

    # Enrich and return
    from app.api.permissions import enrich_permission
    return await enrich_permission(db, perm)


@router.get("/{user_id}/effective-permissions", response_model=EffectivePermissionsResponse)
async def get_user_effective_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all effective permissions for a user.

    Groups permissions by:
    - Sites administered (manage)
    - Sites with write access
    - Sites with read access
    - Direct permissions (not via groups)
    - Group memberships

    Only admins or the user themselves can view effective permissions.
    """
    # Verify target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if current user can view this (admin or self)
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own effective permissions"
        )

    # Import required models
    from app.models import Group, Site
    from app.models.permission import GranteeType, Effect
    from app.services.permission_service import get_user_groups
    from datetime import datetime

    # 1. Get user's group memberships
    group_ids = await get_user_groups(db, user_id)

    # Get group details
    groups = []
    if group_ids:
        groups_result = await db.execute(
            select(Group).where(Group.id.in_(group_ids))
        )
        groups = [GroupBasic(id=g.id, name=g.name) for g in groups_result.scalars().all()]

    # 2. Get all permissions where user or their groups are grantees
    from sqlalchemy import or_, and_

    grantee_conditions = [
        and_(
            ResourcePermission.grantee_type == GranteeType.USER,
            ResourcePermission.grantee_id == user_id
        )
    ]

    for group_id in group_ids:
        grantee_conditions.append(
            and_(
                ResourcePermission.grantee_type == GranteeType.GROUP,
                ResourcePermission.grantee_id == group_id
            )
        )

    permissions_result = await db.execute(
        select(ResourcePermission)
        .where(
            and_(
                or_(*grantee_conditions),
                ResourcePermission.effect == Effect.ALLOW,
                ResourcePermission.permission != Permission.MEMBER,  # Exclude group memberships
                or_(
                    ResourcePermission.expires_at.is_(None),
                    ResourcePermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    permissions = permissions_result.scalars().all()

    # 3. Categorize permissions
    sites_administered = []
    sites_write = []
    sites_read = []
    direct_permissions = []

    # Get group names for lookups
    group_name_map = {g.id: g.name for g in groups}

    for perm in permissions:
        # Get resource name
        resource_name = "Unknown"
        if perm.resource_type == ResourceType.SITE:
            site_result = await db.execute(
                select(Site).where(Site.id == perm.resource_id)
            )
            site = site_result.scalar_one_or_none()
            if site:
                resource_name = site.name
        else:
            # For other resource types, try to get name from their tables
            from app.models import Plan, Sensor, Dashboard

            if perm.resource_type == ResourceType.PLAN:
                res_result = await db.execute(select(Plan).where(Plan.id == perm.resource_id))
                res = res_result.scalar_one_or_none()
                if res:
                    resource_name = res.name
            elif perm.resource_type == ResourceType.SENSOR:
                res_result = await db.execute(select(Sensor).where(Sensor.id == perm.resource_id))
                res = res_result.scalar_one_or_none()
                if res:
                    resource_name = res.name
            elif perm.resource_type == ResourceType.DASHBOARD:
                res_result = await db.execute(select(Dashboard).where(Dashboard.id == perm.resource_id))
                res = res_result.scalar_one_or_none()
                if res:
                    resource_name = res.name

        # Determine source
        is_direct = perm.grantee_type == GranteeType.USER and perm.grantee_id == user_id
        source = "direct" if is_direct else group_name_map.get(perm.grantee_id, "Unknown Group")

        # Categorize by resource type and permission level
        if perm.resource_type == ResourceType.SITE:
            resource_entry = ResourceWithSource(
                resource_type=perm.resource_type.value,
                resource_id=perm.resource_id,
                resource_name=resource_name,
                permission=perm.permission.value,
                source=source
            )

            if perm.permission == Permission.MANAGE:
                sites_administered.append(resource_entry)
            elif perm.permission == Permission.WRITE:
                sites_write.append(resource_entry)
            elif perm.permission == Permission.READ:
                sites_read.append(resource_entry)
        else:
            # Non-site permissions go to direct permissions
            if is_direct:
                # Determine source detail
                source_detail = "direct grant"
                if perm.granted_by == user_id:
                    source_detail = "creator"

                direct_permissions.append(DirectPermission(
                    resource_type=perm.resource_type.value,
                    resource_id=perm.resource_id,
                    resource_name=resource_name,
                    permission=perm.permission.value,
                    source=source_detail
                ))

    return EffectivePermissionsResponse(
        user=UserBasic(id=target_user.id, username=target_user.username),
        groups=groups,
        sites_administered=sites_administered,
        sites_write=sites_write,
        sites_read=sites_read,
        direct_permissions=direct_permissions
    )
