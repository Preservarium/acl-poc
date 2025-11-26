from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

# Security scheme
security = HTTPBearer()


async def raise_permission_denied(
    db: AsyncSession,
    user: User,
    resource_type: str,
    resource_id: str,
    required_permission: str,
    resource_name: Optional[str] = None
) -> None:
    """
    Raise a 403 Forbidden exception with detailed permission information.

    Args:
        db: Database session
        user: Current user
        resource_type: Type of resource (site, plan, sensor, etc.)
        resource_id: ID of the resource
        required_permission: Permission that was required but denied
        resource_name: Optional name of the resource

    Raises:
        HTTPException: 403 with permission details in response body
    """
    from app.services.permission_service import get_effective_permissions, get_user_groups
    from app.models.permission import Permission, GranteeType
    from app.models.group import Group

    # Get all permissions the user has on this resource
    user_perms = await get_effective_permissions(
        db,
        user.id,
        resource_type,
        resource_id
    )

    # Get group names for better display
    group_ids = await get_user_groups(db, user.id)
    group_names = {}
    if group_ids:
        result = await db.execute(select(Group).where(Group.id.in_(group_ids)))
        for group in result.scalars().all():
            group_names[group.id] = group.name

    # Build the permission sources list
    permission_sources = []
    seen_permissions = set()

    for perm_info in user_perms:
        # Only process ALLOW permissions
        if perm_info['effect'] != 'allow':
            continue

        perm_name = perm_info['permission']
        if perm_name not in seen_permissions:
            seen_permissions.add(perm_name)

            # Parse the source to determine via
            source = perm_info.get('source', '')
            via = 'me'
            via_type = 'direct'

            if source.startswith('group:'):
                # Format: "group:group_id" or "group:group_id via resource_type:resource_id"
                parts = source.split(' ')
                group_id = parts[0].split(':')[1]
                via = group_names.get(group_id, f"Group {group_id}")
                via_type = 'group'
            elif source.startswith('user:'):
                via = 'me'
                via_type = 'direct'

            permission_sources.append({
                'permission': perm_name,
                'allowed': True,
                'via': via,
                'via_type': via_type
            })

    # Add the required permission as denied if not already present
    if required_permission not in seen_permissions:
        permission_sources.append({
            'permission': required_permission,
            'allowed': False,
            'via': '',
            'via_type': 'direct'
        })

    # Build detail message
    action_verb = {
        Permission.READ: 'view',
        Permission.WRITE: 'edit',
        Permission.DELETE: 'delete',
        Permission.CREATE: 'create',
        Permission.MANAGE: 'manage'
    }.get(required_permission, 'access')

    detail_msg = f"You don't have permission to {action_verb} this {resource_type}"

    # Create the error response
    error_detail = {
        'detail': detail_msg,
        'required_permission': required_permission,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'resource_name': resource_name,
        'user_permissions': permission_sources
    }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_detail
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current authenticated admin user.

    Raises:
        HTTPException: If user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
