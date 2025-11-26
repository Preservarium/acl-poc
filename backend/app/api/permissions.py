"""Permissions API endpoints."""

import json
from datetime import datetime

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import Group, Plan, ResourcePermission, Sensor, Site, User
from app.models.permission import Permission as PermissionEnum, ResourceType
from app.schemas import (
    ExpiringPermissionResponse,
    MatrixGrantee,
    MatrixPermissionInfo,
    MatrixRow,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCheckResult,
    PermissionCreate,
    PermissionMatrixResponse,
    PermissionResponse,
)
from app.services.audit_service import AuditService
from app.services.permission_service import PermissionService
from app.tasks.permission_expiration import get_expiring_permissions
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/permissions", tags=["permissions"])


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


async def get_grantee_name(db: AsyncSession, grantee_type: str, grantee_id: str) -> str | None:
    """Get the name of a grantee (user or group)."""
    if grantee_type == "user":
        result = await db.execute(select(User).where(User.id == grantee_id))
        user = result.scalar_one_or_none()
        return user.username if user else None
    if grantee_type == "group":
        result = await db.execute(select(Group).where(Group.id == grantee_id))
        group = result.scalar_one_or_none()
        return group.name if group else None
    return None


async def get_resource_name(db: AsyncSession, resource_type: str, resource_id: str) -> str | None:
    """Get the name of a resource."""
    from app.models import Alarm, Alert, Broker, Dashboard

    if resource_type == "site":
        result = await db.execute(select(Site).where(Site.id == resource_id))
        site = result.scalar_one_or_none()
        return site.name if site else None
    if resource_type == "plan":
        result = await db.execute(select(Plan).where(Plan.id == resource_id))
        plan = result.scalar_one_or_none()
        return plan.name if plan else None
    if resource_type == "sensor":
        result = await db.execute(select(Sensor).where(Sensor.id == resource_id))
        sensor = result.scalar_one_or_none()
        return sensor.name if sensor else None
    if resource_type == "broker":
        result = await db.execute(select(Broker).where(Broker.id == resource_id))
        broker = result.scalar_one_or_none()
        return broker.name if broker else None
    if resource_type == "alarm":
        result = await db.execute(select(Alarm).where(Alarm.id == resource_id))
        alarm = result.scalar_one_or_none()
        return alarm.name if alarm else None
    if resource_type == "alert":
        result = await db.execute(select(Alert).where(Alert.id == resource_id))
        alert = result.scalar_one_or_none()
        return f"Alert {alert.id[:8]}" if alert else None
    if resource_type == "dashboard":
        result = await db.execute(select(Dashboard).where(Dashboard.id == resource_id))
        dashboard = result.scalar_one_or_none()
        return dashboard.name if dashboard else None
    if resource_type == "group":
        result = await db.execute(select(Group).where(Group.id == resource_id))
        group = result.scalar_one_or_none()
        return group.name if group else None
    if resource_type == "user":
        result = await db.execute(select(User).where(User.id == resource_id))
        user = result.scalar_one_or_none()
        return user.username if user else None
    return None


async def enrich_permission(db: AsyncSession, perm: ResourcePermission) -> PermissionResponse:
    """Enrich a permission with grantee and resource names."""
    grantee_name = await get_grantee_name(db, perm.grantee_type.value, perm.grantee_id)
    resource_name = await get_resource_name(db, perm.resource_type.value, perm.resource_id)

    # Get fields - SQLAlchemy JSON type handles deserialization automatically
    # but may need additional parsing if double-encoded from seed data
    fields = perm.fields
    if fields and isinstance(fields, str):
        try:
            # Handle double-encoded JSON from seed data
            fields = json.loads(fields)
        except (json.JSONDecodeError, TypeError):
            pass

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
        fields=fields,
        expires_at=perm.expires_at,
        granted_by=perm.granted_by,
        granted_at=perm.granted_at,
    )


@router.get("", response_model=list[PermissionResponse])
async def list_my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all permissions granted to the current user (directly or through groups)."""
    perm_service = PermissionService(db)

    # Get user's permissions
    user_perms = await perm_service.list_for_user(current_user.id)

    # Get user's groups via the ACL system
    user_groups = await current_user.get_groups(db)
    group_ids = [group.id for group in user_groups]

    # Get group permissions
    group_perms = []
    if group_ids:
        result = await db.execute(
            select(ResourcePermission).where(and_(ResourcePermission.grantee_type == "group", ResourcePermission.grantee_id.in_(group_ids)))
        )
        group_perms = result.scalars().all()

    all_perms = list(user_perms) + list(group_perms)

    # Enrich with names
    enriched = []
    for perm in all_perms:
        enriched.append(await enrich_permission(db, perm))

    return enriched


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[PermissionResponse])
async def list_resource_permissions(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all permissions for a specific resource.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Check if user has manage permission on the resource
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {resource_type}")

    has_permission = await perm_service.check(current_user, rt, resource_id, PermissionEnum.MANAGE)

    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view permissions for this resource")

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
    """Grant a permission to a user or group.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Check if current user has manage permission on the resource
    has_permission = await perm_service.check(current_user, perm_create.resource_type, perm_create.resource_id, PermissionEnum.MANAGE)

    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to grant permissions on this resource")

    # Verify grantee exists
    if perm_create.grantee_type.value == "user":
        result = await db.execute(select(User).where(User.id == perm_create.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    elif perm_create.grantee_type.value == "group":
        result = await db.execute(select(Group).where(Group.id == perm_create.grantee_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Verify resource exists
    if perm_create.resource_type.value == "user":
        result = await db.execute(select(User).where(User.id == perm_create.resource_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    elif perm_create.resource_type.value == "group":
        result = await db.execute(select(Group).where(Group.id == perm_create.resource_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target group not found")

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

    # Log audit event
    audit_service = AuditService(db)
    await audit_service.log_permission_granted(
        actor_id=current_user.id,
        target_user_id=perm_create.grantee_id if perm_create.grantee_type.value == "user" else None,
        target_group_id=perm_create.grantee_id if perm_create.grantee_type.value == "group" else None,
        resource_type=perm_create.resource_type.value,
        resource_id=perm_create.resource_id,
        permission=perm_create.permission.value,
        details={
            "effect": perm_create.effect.value,
            "inherit": perm_create.inherit,
            "fields": perm_create.fields,
            "expires_at": perm_create.expires_at.isoformat() if perm_create.expires_at else None,
        },
    )

    # Enrich and return
    return await enrich_permission(db, permission)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a permission.

    Requires 'manage' permission on the resource.
    """
    perm_service = PermissionService(db)

    # Get the permission to check
    result = await db.execute(select(ResourcePermission).where(ResourcePermission.id == permission_id))
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    # Check if current user has manage permission on the resource
    has_permission = await perm_service.check(current_user, permission.resource_type, permission.resource_id, PermissionEnum.MANAGE)

    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to revoke permissions on this resource")

    # Store permission details before revoking for audit log
    grantee_type = permission.grantee_type.value
    grantee_id = permission.grantee_id
    resource_type = permission.resource_type.value
    resource_id = permission.resource_id
    perm_name = permission.permission.value

    # Revoke
    success = await perm_service.revoke(permission_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    # Log audit event
    audit_service = AuditService(db)
    await audit_service.log_permission_revoked(
        actor_id=current_user.id,
        target_user_id=grantee_id if grantee_type == "user" else None,
        target_group_id=grantee_id if grantee_type == "group" else None,
        resource_type=resource_type,
        resource_id=resource_id,
        permission=perm_name,
        details={
            "grantee_type": grantee_type,
        },
    )


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permissions(
    check_request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk check permissions for the current user."""
    perm_service = PermissionService(db)

    results = []
    for check in check_request.checks:
        allowed = await perm_service.check(current_user, check.resource_type, check.resource_id, check.permission)

        results.append(
            PermissionCheckResult(
                resource_type=check.resource_type,
                resource_id=check.resource_id,
                permission=check.permission,
                allowed=allowed,
            )
        )

    return PermissionCheckResponse(results=results)


@router.get("/resource/{resource_type}/{resource_id}/effective")
async def get_effective_permissions(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get effective permissions for the current user on a resource.

    Shows what permissions the user has and where they come from.
    """
    from app.services.permission_service import get_effective_permissions as get_eff_perms

    # Validate resource type
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {resource_type}")

    # Get effective permissions
    perms = await get_eff_perms(db, current_user.id, resource_type, resource_id)

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": await get_resource_name(db, resource_type, resource_id),
        "permissions": perms,
    }


@router.get("/inheritance/{resource_type}/{resource_id}")
async def get_inheritance_chain(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View the inheritance chain for a resource.

    Shows the resource's ancestors from which it can inherit permissions.
    """
    from app.services.hierarchy import get_ancestors

    # Validate resource type
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {resource_type}")

    # Get ancestors
    ancestors = await get_ancestors(db, resource_type, resource_id)

    # Enrich with names
    enriched_chain = []
    for res_type, res_id, depth in ancestors:
        name = await get_resource_name(db, res_type, res_id)
        enriched_chain.append({"resource_type": res_type, "resource_id": res_id, "resource_name": name, "depth": depth})

    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": await get_resource_name(db, resource_type, resource_id),
        "inheritance_chain": enriched_chain,
    }


@router.get("/user-inheritance/{user_id}")
async def get_user_inheritance_tree(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the full permission inheritance tree for a user.

    Returns a hierarchical tree showing:
    - User's group memberships
    - All resources the user has permissions on (direct or inherited)
    - Permission sources (direct, via group, inherited from parent)
    - DENY permissions that block access
    """
    from datetime import datetime

    from app.models import Alarm, Alert, Broker
    from app.models.permission import GranteeType
    from app.services.permission_service import get_user_groups

    # Verify target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check permissions (admin or self)
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own inheritance tree")

    # Get user's groups
    group_ids = await get_user_groups(db, user_id)
    groups = []
    if group_ids:
        groups_result = await db.execute(select(Group).where(Group.id.in_(group_ids)))
        groups = [{"id": g.id, "name": g.name} for g in groups_result.scalars().all()]

    # Build grantee conditions
    grantee_conditions = [and_(ResourcePermission.grantee_type == GranteeType.USER, ResourcePermission.grantee_id == user_id)]
    for group_id in group_ids:
        grantee_conditions.append(and_(ResourcePermission.grantee_type == GranteeType.GROUP, ResourcePermission.grantee_id == group_id))

    # Get all permissions for user and their groups
    permissions_result = await db.execute(
        select(ResourcePermission).where(
            and_(or_(*grantee_conditions), or_(ResourcePermission.expires_at.is_(None), ResourcePermission.expires_at > datetime.utcnow()))
        )
    )
    all_permissions = permissions_result.scalars().all()

    # Build resource tree structure
    # First, get all sites
    sites_result = await db.execute(select(Site))
    all_sites = sites_result.scalars().all()

    tree_nodes = []

    for site in all_sites:
        # Check if user has any permissions on this site or its descendants
        site_perms = [p for p in all_permissions if p.resource_type.value == "site" and p.resource_id == site.id]

        # Get site's children (plans)
        plans_result = await db.execute(select(Plan).where(Plan.site_id == site.id))
        plans = plans_result.scalars().all()

        plan_nodes = []
        for plan in plans:
            plan_perms = [p for p in all_permissions if p.resource_type.value == "plan" and p.resource_id == plan.id]

            # Get plan's children (sensors and brokers)
            sensors_result = await db.execute(select(Sensor).where(Sensor.plan_id == plan.id))
            sensors = sensors_result.scalars().all()

            brokers_result = await db.execute(select(Broker).where(Broker.plan_id == plan.id))
            brokers = brokers_result.scalars().all()

            children = []

            # Process sensors
            for sensor in sensors:
                sensor_perms = [p for p in all_permissions if p.resource_type.value == "sensor" and p.resource_id == sensor.id]

                # Get sensor's alarms
                alarms_result = await db.execute(select(Alarm).where(Alarm.sensor_id == sensor.id))
                alarms = alarms_result.scalars().all()

                alarm_nodes = []
                for alarm in alarms:
                    alarm_perms = [p for p in all_permissions if p.resource_type.value == "alarm" and p.resource_id == alarm.id]

                    # Get alarm's alerts
                    alerts_result = await db.execute(select(Alert).where(Alert.alarm_id == alarm.id))
                    alerts = alerts_result.scalars().all()

                    alert_nodes = []
                    for alert in alerts:
                        alert_perms = [p for p in all_permissions if p.resource_type.value == "alert" and p.resource_id == alert.id]

                        # Compute effective permissions for alert
                        alert_effective = await compute_effective_permissions(db, user_id, "alert", alert.id, alert_perms, all_permissions, groups)

                        if alert_effective["permissions"] or alert_effective["denies"]:
                            alert_nodes.append(
                                {
                                    "id": alert.id,
                                    "name": f"Alert {alert.id[:8]}",
                                    "type": "alert",
                                    "permissions": alert_effective["permissions"],
                                    "denies": alert_effective["denies"],
                                    "children": [],
                                }
                            )

                    # Compute effective permissions for alarm
                    alarm_effective = await compute_effective_permissions(db, user_id, "alarm", alarm.id, alarm_perms, all_permissions, groups)

                    if alarm_effective["permissions"] or alarm_effective["denies"] or alert_nodes:
                        alarm_nodes.append(
                            {
                                "id": alarm.id,
                                "name": alarm.name,
                                "type": "alarm",
                                "permissions": alarm_effective["permissions"],
                                "denies": alarm_effective["denies"],
                                "children": alert_nodes,
                            }
                        )

                # Compute effective permissions for sensor
                sensor_effective = await compute_effective_permissions(db, user_id, "sensor", sensor.id, sensor_perms, all_permissions, groups)

                if sensor_effective["permissions"] or sensor_effective["denies"] or alarm_nodes:
                    children.append(
                        {
                            "id": sensor.id,
                            "name": sensor.name,
                            "type": "sensor",
                            "permissions": sensor_effective["permissions"],
                            "denies": sensor_effective["denies"],
                            "children": alarm_nodes,
                        }
                    )

            # Process brokers
            for broker in brokers:
                broker_perms = [p for p in all_permissions if p.resource_type.value == "broker" and p.resource_id == broker.id]

                # Compute effective permissions for broker
                broker_effective = await compute_effective_permissions(db, user_id, "broker", broker.id, broker_perms, all_permissions, groups)

                if broker_effective["permissions"] or broker_effective["denies"]:
                    children.append(
                        {
                            "id": broker.id,
                            "name": broker.name,
                            "type": "broker",
                            "permissions": broker_effective["permissions"],
                            "denies": broker_effective["denies"],
                            "children": [],
                        }
                    )

            # Compute effective permissions for plan
            plan_effective = await compute_effective_permissions(db, user_id, "plan", plan.id, plan_perms, all_permissions, groups)

            if plan_effective["permissions"] or plan_effective["denies"] or children:
                plan_nodes.append(
                    {
                        "id": plan.id,
                        "name": plan.name,
                        "type": "plan",
                        "permissions": plan_effective["permissions"],
                        "denies": plan_effective["denies"],
                        "children": children,
                    }
                )

        # Compute effective permissions for site
        site_effective = await compute_effective_permissions(db, user_id, "site", site.id, site_perms, all_permissions, groups)

        if site_effective["permissions"] or site_effective["denies"] or plan_nodes:
            tree_nodes.append(
                {
                    "id": site.id,
                    "name": site.name,
                    "type": "site",
                    "permissions": site_effective["permissions"],
                    "denies": site_effective["denies"],
                    "children": plan_nodes,
                }
            )

    return {"user": {"id": target_user.id, "username": target_user.username}, "groups": groups, "tree": tree_nodes}


async def compute_effective_permissions(
    db: AsyncSession, user_id: str, resource_type: str, resource_id: str, direct_perms: list, all_permissions: list, groups: list
) -> dict:
    """Compute effective permissions for a resource considering inheritance.

    Returns:
        dict with 'permissions' (list of allow perms) and 'denies' (list of deny perms)
    """
    from app.services.hierarchy import get_ancestors

    # Get ancestors for inheritance
    ancestors = await get_ancestors(db, resource_type, resource_id)

    # Collect all applicable permissions (direct and inherited)
    applicable_perms = []

    for res_type, res_id, depth in ancestors:
        matching_perms = [p for p in all_permissions if p.resource_type.value == res_type and p.resource_id == res_id]

        for perm in matching_perms:
            # Skip non-inheritable permissions on ancestors
            if depth > 0 and not perm.inherit:
                continue

            # Determine source
            source = None
            is_inherited = depth > 0

            if perm.grantee_type.value == "user":
                source = "direct"
            else:
                # Find group name
                group_name = next((g["name"] for g in groups if g["id"] == perm.grantee_id), "Unknown Group")
                source = f"via {group_name}"

            applicable_perms.append(
                {
                    "permission": perm.permission.value,
                    "effect": perm.effect.value,
                    "fields": parse_fields(perm.fields),
                    "inherit": perm.inherit,
                    "source": source,
                    "is_inherited": is_inherited,
                    "depth": depth,
                }
            )

    # Separate allows and denies
    allows = [p for p in applicable_perms if p["effect"] == "allow"]
    denies = [p for p in applicable_perms if p["effect"] == "deny"]

    return {"permissions": allows, "denies": denies}


@router.get("/matrix", response_model=PermissionMatrixResponse)
async def get_permission_matrix(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a permission matrix for a specific resource.

    Shows a grid with grantees as rows and permissions as columns,
    indicating which permissions each grantee has on the resource
    (including inherited permissions).

    Requires 'manage' permission on the resource.
    """
    from app.models.permission import Effect
    from app.services.hierarchy import get_ancestors

    # Validate resource type
    try:
        rt = ResourceType(resource_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {resource_type}")

    # Check if user has manage permission on the resource
    perm_service = PermissionService(db)
    has_permission = await perm_service.check(current_user, rt, resource_id, PermissionEnum.MANAGE)

    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view the permission matrix for this resource")

    # Get resource name
    resource_name = await get_resource_name(db, resource_type, resource_id)
    if not resource_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # Get all permissions for this resource and its ancestors
    ancestors = await get_ancestors(db, resource_type, resource_id)

    # Query all permissions for this resource and ancestors
    all_perms_result = await db.execute(
        select(ResourcePermission).where(
            or_(*[and_(ResourcePermission.resource_type == res_type, ResourcePermission.resource_id == res_id) for res_type, res_id, _ in ancestors])
        )
    )
    all_permissions = all_perms_result.scalars().all()

    # Group permissions by grantee
    grantee_permissions = {}

    for perm in all_permissions:
        # Determine if this permission is inherited
        is_direct = perm.resource_type.value == resource_type and perm.resource_id == resource_id
        depth = next((d for rt, ri, d in ancestors if rt == perm.resource_type.value and ri == perm.resource_id), None)

        # Skip non-inheritable permissions on ancestors
        if depth is not None and depth > 0 and not perm.inherit:
            continue

        grantee_key = f"{perm.grantee_type.value}:{perm.grantee_id}"

        if grantee_key not in grantee_permissions:
            grantee_permissions[grantee_key] = {"grantee_type": perm.grantee_type, "grantee_id": perm.grantee_id, "permissions": {}}

        perm_type = perm.permission.value

        # Initialize permission info if not exists
        if perm_type not in grantee_permissions[grantee_key]["permissions"]:
            grantee_permissions[grantee_key]["permissions"][perm_type] = {
                "allowed": False,
                "inherited": False,
                "has_field_restrictions": False,
                "fields": None,
                "source": None,
            }

        # Update permission info
        perm_info = grantee_permissions[grantee_key]["permissions"][perm_type]

        # Only ALLOW effects grant permissions
        if perm.effect == Effect.ALLOW:
            perm_info["allowed"] = True

            if not is_direct:
                perm_info["inherited"] = True
                # Get parent resource name for source
                parent_name = await get_resource_name(db, perm.resource_type.value, perm.resource_id)
                perm_info["source"] = f"{perm.resource_type.value}: {parent_name}"

            parsed_fields = parse_fields(perm.fields)
            if parsed_fields is not None:
                perm_info["has_field_restrictions"] = True
                # Merge fields if multiple permissions exist
                if perm_info["fields"] is None:
                    perm_info["fields"] = parsed_fields
                else:
                    perm_info["fields"] = list(set(perm_info["fields"] + parsed_fields))

    # Build matrix rows
    matrix_rows = []

    for grantee_key, grantee_data in grantee_permissions.items():
        # Get grantee name
        grantee_name = await get_grantee_name(db, grantee_data["grantee_type"].value, grantee_data["grantee_id"])

        if not grantee_name:
            grantee_name = grantee_data["grantee_id"]

        # Create permission info objects for all permission types
        permissions_dict = {}
        for perm_type in ["read", "write", "delete", "create", "manage"]:
            if perm_type in grantee_data["permissions"]:
                perm_data = grantee_data["permissions"][perm_type]
                permissions_dict[perm_type] = MatrixPermissionInfo(**perm_data)
            else:
                # Not granted
                permissions_dict[perm_type] = MatrixPermissionInfo(allowed=False)

        matrix_rows.append(
            MatrixRow(
                grantee=MatrixGrantee(grantee_id=grantee_data["grantee_id"], grantee_name=grantee_name, grantee_type=grantee_data["grantee_type"]),
                permissions=permissions_dict,
            )
        )

    # Sort rows: groups first, then users; alphabetically within each type
    matrix_rows.sort(key=lambda x: (0 if x.grantee.grantee_type.value == "group" else 1, x.grantee.grantee_name.lower()))

    return PermissionMatrixResponse(resource_type=resource_type, resource_id=resource_id, resource_name=resource_name, grantees=matrix_rows)


@router.get("/expiring", response_model=list[ExpiringPermissionResponse])
async def list_expiring_permissions(
    days_ahead: int = Query(default=7, ge=1, le=90, description="Number of days to look ahead"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of permissions expiring within the specified number of days.

    This endpoint is typically used by admins to monitor and manage
    permissions that are about to expire.

    Args:
        days_ahead: Number of days to look ahead (default: 7, max: 90)

    Returns:
        List of permissions that will expire within the specified timeframe
    """
    # Only allow admins to view expiring permissions
    # In a production system, you might want to allow users to see their own expiring permissions
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can view expiring permissions")

    # Get expiring permissions
    expiring_perms = await get_expiring_permissions(db, days_ahead)

    if not expiring_perms:
        return []

    # Enrich with names and calculate days until expiry
    now = datetime.utcnow()
    enriched = []

    for perm in expiring_perms:
        grantee_name = await get_grantee_name(db, perm.grantee_type.value, perm.grantee_id)
        resource_name = await get_resource_name(db, perm.resource_type.value, perm.resource_id)

        days_until_expiry = (perm.expires_at - now).days

        enriched.append(
            ExpiringPermissionResponse(
                id=perm.id,
                grantee_type=perm.grantee_type,
                grantee_id=perm.grantee_id,
                grantee_name=grantee_name,
                resource_type=perm.resource_type,
                resource_id=perm.resource_id,
                resource_name=resource_name,
                permission=perm.permission,
                effect=perm.effect,
                expires_at=perm.expires_at,
                granted_at=perm.granted_at,
                granted_by=perm.granted_by,
                days_until_expiry=days_until_expiry,
            )
        )

    return enriched
