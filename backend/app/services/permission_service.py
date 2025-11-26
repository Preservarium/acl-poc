from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.user import User
from app.models.group import Group
from app.models.permission import (
    ResourcePermission,
    GranteeType,
    ResourceType,
    Permission,
    Effect
)
from app.models.site import Site
from app.models.plan import Plan
from app.models.sensor import Sensor
from app.services.hierarchy import get_ancestors, HIERARCHY_CONFIG
from app.schemas.permission import PermissionMetadata
from app.services.cache_service import cache


# Resource defaults - default permissions for resource types
# System config resources are readable by authenticated users, writable only by admins
RESOURCE_DEFAULTS = {
    ResourceType.HARDWARE: {
        Permission.READ: True,  # Any authenticated user can read
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
    ResourceType.DATATYPE: {
        Permission.READ: True,
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
    ResourceType.PROTOCOL: {
        Permission.READ: True,
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
    ResourceType.PARSER: {
        Permission.READ: True,
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
    ResourceType.MANUFACTURER: {
        Permission.READ: True,
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
    ResourceType.COMMUNICATION_MODE: {
        Permission.READ: True,
        Permission.WRITE: 'admin_only',
        Permission.DELETE: 'admin_only',
        Permission.CREATE: 'admin_only',
    },
}


# Permission hierarchy - higher permissions imply lower ones
# When checking for a permission, we also accept any higher permission
# Example: checking 'read' will pass if user has 'write', 'delete', 'create', or 'manage'
PERMISSION_HIERARCHY = {
    Permission.READ: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE, Permission.MANAGE],
    Permission.WRITE: [Permission.WRITE, Permission.MANAGE],
    Permission.DELETE: [Permission.DELETE, Permission.MANAGE],
    Permission.CREATE: [Permission.CREATE, Permission.MANAGE],
    Permission.MANAGE: [Permission.MANAGE],
}


def expand_permission(permission: Permission) -> List[Permission]:
    """
    Expand a permission to include all permissions that imply it.

    This implements the permission hierarchy where higher permissions imply lower ones:
    - manage implies create, delete, write, read
    - write implies read
    - delete implies read
    - create implies read

    Args:
        permission: The permission to expand

    Returns:
        List of permissions that satisfy the requested permission

    Example:
        >>> expand_permission(Permission.READ)
        [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE, Permission.MANAGE]
        >>> expand_permission(Permission.MANAGE)
        [Permission.MANAGE]
    """
    return PERMISSION_HIERARCHY.get(permission, [permission])


async def get_user_groups(db: AsyncSession, user_id: str) -> List[str]:
    """
    Get all group IDs that a user is a member of.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of group IDs the user is a member of
    """
    # Try cache first
    cached_groups = await cache.get_user_groups(user_id)
    if cached_groups is not None:
        return cached_groups

    # Cache miss - fetch from database
    result = await db.execute(
        select(ResourcePermission.resource_id)
        .where(
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.grantee_id == user_id,
                ResourcePermission.resource_type == ResourceType.GROUP,
                ResourcePermission.permission == Permission.MEMBER,
                ResourcePermission.effect == Effect.ALLOW,
                or_(
                    ResourcePermission.expires_at.is_(None),
                    ResourcePermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    group_ids = [row[0] for row in result.all()]

    # Cache the result
    await cache.set_user_groups(user_id, group_ids)

    return group_ids


async def get_effective_permissions(
    db: AsyncSession,
    user_id: str,
    resource_type: str,
    resource_id: str
) -> List[dict]:
    """
    Get all effective permissions for a user on a resource with their sources.

    Args:
        db: Database session
        user_id: ID of the user
        resource_type: Type of resource
        resource_id: ID of the resource

    Returns:
        List of permission dictionaries with source information
    """
    # Get user's groups
    group_ids = await get_user_groups(db, user_id)

    # Build grantee list
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

    # Get ancestors
    ancestors = await get_ancestors(db, resource_type, resource_id)

    # Query all applicable permissions
    result = await db.execute(
        select(ResourcePermission)
        .where(
            and_(
                or_(*grantee_conditions),
                or_(*[
                    and_(
                        ResourcePermission.resource_type == res_type,
                        ResourcePermission.resource_id == res_id
                    )
                    for res_type, res_id, _ in ancestors
                ]),
                or_(
                    ResourcePermission.expires_at.is_(None),
                    ResourcePermission.expires_at > datetime.utcnow()
                )
            )
        )
    )
    permissions = result.scalars().all()

    # Format results with source information
    effective_perms = []
    for perm in permissions:
        # Find depth
        depth = next(
            (d for rt, ri, d in ancestors if rt == perm.resource_type.value and ri == perm.resource_id),
            None
        )

        if depth is None:
            continue

        # Skip non-inheritable permissions on ancestors
        if depth > 0 and not perm.inherit:
            continue

        source = f"{perm.grantee_type.value}:{perm.grantee_id}"
        if depth > 0:
            source += f" via {perm.resource_type.value}:{perm.resource_id}"

        effective_perms.append({
            'permission': perm.permission.value,
            'effect': perm.effect.value,
            'fields': perm.fields,
            'inherit': perm.inherit,
            'source': source,
            'depth': depth,
            'expires_at': perm.expires_at.isoformat() if perm.expires_at else None
        })

    return effective_perms


class PermissionService:
    """Service for permission operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Check if a user has a specific permission on a resource.

        Args:
            user: The User object
            resource_type: Type of resource
            resource_id: ID of the resource
            permission: Permission to check

        Returns:
            Tuple of (allowed: bool, fields: Optional[List[str]])
            - fields=None means all fields allowed
            - fields=[] means no fields (but permission exists)
            - fields=['a','b'] means only those fields
        """
        # 1. Admin bypass
        if user.is_admin:
            return (True, None)  # All fields

        # 2. Try cache first
        cached_result = await cache.get_permission(
            user.id,
            resource_type.value,
            resource_id,
            permission.value
        )
        if cached_result is not None:
            return cached_result

        # 2. Get user's groups via 'member' permission
        group_ids = await get_user_groups(self.db, user.id)

        # 3. Build grantee list
        grantee_conditions = [
            and_(
                ResourcePermission.grantee_type == GranteeType.USER,
                ResourcePermission.grantee_id == user.id
            )
        ]
        for group_id in group_ids:
            grantee_conditions.append(
                and_(
                    ResourcePermission.grantee_type == GranteeType.GROUP,
                    ResourcePermission.grantee_id == group_id
                )
            )

        # 4. Get ancestors (uses HIERARCHY_CONFIG)
        ancestors = await get_ancestors(self.db, resource_type.value, resource_id)

        # 5. Expand permission using hierarchy (manage > create/delete/write > read)
        perms_to_check = expand_permission(permission)

        # 6. Single query for all applicable permissions
        result = await self.db.execute(
            select(ResourcePermission)
            .where(
                and_(
                    or_(*grantee_conditions),
                    or_(*[
                        and_(
                            ResourcePermission.resource_type == res_type,
                            ResourcePermission.resource_id == res_id
                        )
                        for res_type, res_id, _ in ancestors
                    ]),
                    ResourcePermission.permission.in_(perms_to_check),
                    or_(
                        ResourcePermission.expires_at.is_(None),
                        ResourcePermission.expires_at > datetime.utcnow()
                    )
                )
            )
            .order_by(ResourcePermission.effect.desc())  # DENY before ALLOW
        )
        permissions = result.scalars().all()

        # 7. Resolve with field aggregation
        allowed_fields = []

        for perm in permissions:
            # Find depth for this permission's resource
            depth = next(
                (d for rt, ri, d in ancestors if rt == perm.resource_type.value and ri == perm.resource_id),
                None
            )

            if depth is None:
                continue

            # Skip non-inheritable permissions on ancestors
            if depth > 0 and not perm.inherit:
                continue

            if perm.effect == Effect.DENY:
                result = (False, None)
                # Cache the result
                await cache.set_permission(
                    user.id,
                    resource_type.value,
                    resource_id,
                    permission.value,
                    result[0],
                    result[1]
                )
                return result

            if perm.effect == Effect.ALLOW:
                if perm.fields is None:
                    result = (True, None)  # All fields
                    # Cache the result
                    await cache.set_permission(
                        user.id,
                        resource_type.value,
                        resource_id,
                        permission.value,
                        result[0],
                        result[1]
                    )
                    return result
                else:
                    allowed_fields.extend(perm.fields)

        if allowed_fields:
            result = (True, list(set(allowed_fields)))
            # Cache the result
            await cache.set_permission(
                user.id,
                resource_type.value,
                resource_id,
                permission.value,
                result[0],
                result[1]
            )
            return result

        # 8. Check resource defaults before denying
        if resource_type in RESOURCE_DEFAULTS:
            default_policy = RESOURCE_DEFAULTS[resource_type].get(permission)
            if default_policy is True:
                # Any authenticated user can access
                result = (True, None)
                await cache.set_permission(
                    user.id,
                    resource_type.value,
                    resource_id,
                    permission.value,
                    result[0],
                    result[1]
                )
                return result
            elif default_policy == 'admin_only':
                # Only admins (already checked above), so deny for non-admins
                pass

        # 9. Default deny
        result = (False, None)
        # Cache the result
        await cache.set_permission(
            user.id,
            resource_type.value,
            resource_id,
            permission.value,
            result[0],
            result[1]
        )
        return result


    async def grant(
        self,
        grantee_type: GranteeType,
        grantee_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permission: Permission,
        effect: Effect = Effect.ALLOW,
        inherit: bool = True,
        fields: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        granted_by: Optional[str] = None
    ) -> ResourcePermission:
        """
        Grant a permission.

        Args:
            grantee_type: Type of grantee (user or group)
            grantee_id: ID of the grantee
            resource_type: Type of resource
            resource_id: ID of the resource
            permission: Permission to grant
            effect: Effect (allow or deny)
            inherit: Whether permission should inherit to children
            fields: List of field names or None for all fields
            expires_at: Optional expiration datetime
            granted_by: ID of user granting the permission

        Returns:
            Created ResourcePermission object
        """
        perm = ResourcePermission(
            grantee_type=grantee_type,
            grantee_id=grantee_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            effect=effect,
            inherit=inherit,
            fields=fields,
            expires_at=expires_at,
            granted_by=granted_by
        )
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)

        # Invalidate cache
        if grantee_type == GranteeType.USER:
            await cache.invalidate_user_permissions(grantee_id)
        elif grantee_type == GranteeType.GROUP:
            await cache.invalidate_group_permissions(grantee_id)

        # Also invalidate resource-specific cache
        await cache.invalidate_resource_permissions(resource_type.value, resource_id)

        # If granting group membership, invalidate user's group cache
        if resource_type == ResourceType.GROUP and permission == Permission.MEMBER:
            await cache.invalidate_user_permissions(grantee_id)

        return perm

    async def revoke(self, permission_id: str) -> bool:
        """
        Revoke a permission.

        Args:
            permission_id: ID of the permission to revoke

        Returns:
            True if permission was revoked, False if not found
        """
        result = await self.db.execute(
            select(ResourcePermission).where(ResourcePermission.id == permission_id)
        )
        perm = result.scalar_one_or_none()

        if not perm:
            return False

        # Store values before deletion for cache invalidation
        grantee_type = perm.grantee_type
        grantee_id = perm.grantee_id
        resource_type = perm.resource_type
        resource_id = perm.resource_id
        permission = perm.permission

        await self.db.delete(perm)
        await self.db.commit()

        # Invalidate cache
        if grantee_type == GranteeType.USER:
            await cache.invalidate_user_permissions(grantee_id)
        elif grantee_type == GranteeType.GROUP:
            await cache.invalidate_group_permissions(grantee_id)

        # Also invalidate resource-specific cache
        await cache.invalidate_resource_permissions(resource_type.value, resource_id)

        # If revoking group membership, invalidate user's group cache
        if resource_type == ResourceType.GROUP and permission == Permission.MEMBER:
            await cache.invalidate_user_permissions(grantee_id)

        return True

    async def list_for_resource(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> List[ResourcePermission]:
        """
        List all permissions for a resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource

        Returns:
            List of ResourcePermission objects
        """
        result = await self.db.execute(
            select(ResourcePermission)
            .where(
                and_(
                    ResourcePermission.resource_type == resource_type,
                    ResourcePermission.resource_id == resource_id
                )
            )
        )
        return list(result.scalars().all())

    async def list_for_user(self, user_id: str) -> List[ResourcePermission]:
        """
        List all permissions for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of ResourcePermission objects
        """
        result = await self.db.execute(
            select(ResourcePermission)
            .where(
                and_(
                    ResourcePermission.grantee_type == GranteeType.USER,
                    ResourcePermission.grantee_id == user_id
                )
            )
        )
        return list(result.scalars().all())

    async def auto_grant_manage(
        self,
        creator_id: str,
        resource_type: ResourceType,
        resource_id: str
    ) -> ResourcePermission:
        """
        Auto-grant manage permission to creator of a resource.

        Args:
            creator_id: ID of the creator
            resource_type: Type of resource
            resource_id: ID of the resource

        Returns:
            Created ResourcePermission object
        """
        return await self.grant(
            grantee_type=GranteeType.USER,
            grantee_id=creator_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=Permission.MANAGE,
            effect=Effect.ALLOW,
            inherit=True,
            granted_by=None  # System-granted
        )

    async def get_permission_metadata(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str
    ) -> PermissionMetadata:
        """
        Get all permission flags for a user on a resource.

        Args:
            user: The User object
            resource_type: Type of resource
            resource_id: ID of the resource

        Returns:
            PermissionMetadata object with all permission flags
        """
        metadata = PermissionMetadata()

        # Check each permission type
        for perm_name in ['read', 'write', 'delete', 'create', 'manage']:
            perm = Permission[perm_name.upper()]
            allowed, fields = await self.check(user, resource_type, resource_id, perm)
            setattr(metadata, f'can_{perm_name}', allowed)

            # Store writable fields for write permission
            # fields=None means all fields allowed
            # fields=[...] means only specific fields allowed
            # fields=[] means no fields (but this shouldn't happen if allowed=True)
            if perm_name == 'write' and allowed:
                metadata.writable_fields = fields

        return metadata
