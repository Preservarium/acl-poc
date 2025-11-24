from typing import List, Optional, Tuple
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


# Permission hierarchy - higher permissions imply lower ones
PERMISSION_HIERARCHY = {
    Permission.READ: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE, Permission.MANAGE],
    Permission.WRITE: [Permission.WRITE, Permission.MANAGE],
    Permission.DELETE: [Permission.DELETE, Permission.MANAGE],
    Permission.CREATE: [Permission.CREATE, Permission.MANAGE],
    Permission.MANAGE: [Permission.MANAGE],
}


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
    ) -> bool:
        """
        Check if a user has a specific permission on a resource.

        Args:
            user: The User object
            resource_type: Type of resource
            resource_id: ID of the resource
            permission: Permission to check

        Returns:
            True if permission is granted, False otherwise
        """
        # 1. Admin bypass
        if user.is_admin:
            return True

        # 2. Get user's group IDs
        group_ids = [group.id for group in user.groups]

        # 3. Build ancestor chain
        ancestors = await self._get_ancestors(resource_type, resource_id)

        # 4. Expand permission (check implied permissions)
        perms_to_check = PERMISSION_HIERARCHY.get(permission, [permission])

        # 5. Query all applicable permissions
        # Check from closest to furthest ancestor
        for depth, (res_type, res_id) in enumerate(ancestors):
            # Build grantee conditions
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

            # Query permissions
            result = await self.db.execute(
                select(ResourcePermission)
                .where(
                    and_(
                        ResourcePermission.resource_type == res_type,
                        ResourcePermission.resource_id == res_id,
                        ResourcePermission.permission.in_(perms_to_check),
                        or_(*grantee_conditions)
                    )
                )
                .order_by(ResourcePermission.effect.desc())  # DENY before ALLOW
            )
            permissions = result.scalars().all()

            # 6. Resolve (first match wins)
            for perm in permissions:
                # Skip non-inheritable permissions on ancestors
                if depth > 0 and not perm.inherit:
                    continue

                if perm.effect == Effect.DENY:
                    return False
                if perm.effect == Effect.ALLOW:
                    return True

        # 7. Default deny
        return False

    async def _get_ancestors(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> List[Tuple[ResourceType, str]]:
        """
        Get ancestor chain for a resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource

        Returns:
            List of (resource_type, resource_id) tuples, closest first
        """
        result = [(resource_type, resource_id)]

        if resource_type == ResourceType.SENSOR:
            # Get sensor -> plan -> site chain
            sensor_result = await self.db.execute(
                select(Sensor).where(Sensor.id == resource_id)
            )
            sensor = sensor_result.scalar_one_or_none()
            if sensor:
                result.append((ResourceType.PLAN, sensor.plan_id))
                plan_result = await self.db.execute(
                    select(Plan).where(Plan.id == sensor.plan_id)
                )
                plan = plan_result.scalar_one_or_none()
                if plan:
                    result.append((ResourceType.SITE, plan.site_id))

        elif resource_type == ResourceType.PLAN:
            # Get plan -> site chain
            plan_result = await self.db.execute(
                select(Plan).where(Plan.id == resource_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                result.append((ResourceType.SITE, plan.site_id))

        # Site has no parent

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
            granted_by=granted_by
        )
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)
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

        await self.db.delete(perm)
        await self.db.commit()
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
