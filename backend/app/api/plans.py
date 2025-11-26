"""Plans API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Plan, Site, Group, ResourcePermission
from app.models.permission import ResourceType, Permission, GranteeType, Effect
from app.schemas import PlanCreate, PlanResponse
from app.schemas.permission import (
    PlanPermissionsResponse,
    PermissionWithGrantee,
    EffectivePermission,
    ParentInfo,
    PermissionEnum
)
from app.services.permission_service import PermissionService, get_user_groups
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
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
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

    # Convert to response model
    response = PlanResponse.model_validate(plan)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.PLAN,
            plan_id
        )

    return response


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


@router.get("/{plan_id}/permissions", response_model=PlanPermissionsResponse)
async def get_plan_permissions(
    plan_id: str,
    include_inherited: bool = Query(True, description="Include inherited permissions from parent site"),
    include_effective: bool = Query(True, description="Include effective combined permissions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get permissions on this plan.

    Returns:
    - parent: Information about the parent site
    - inherited: Permissions inherited from parent site (if include_inherited=True)
    - direct: Permissions granted directly on this plan
    - effective: Combined effective permissions per user (if include_effective=True)

    Requires 'read' permission on the plan.
    """
    from datetime import datetime
    perm_service = PermissionService(db)

    # Check permission to view plan
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

    # Get plan with site
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    # Get site
    result = await db.execute(
        select(Site).where(Site.id == plan.site_id)
    )
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent site not found"
        )

    # Build response
    response = PlanPermissionsResponse(
        parent=ParentInfo(
            type="site",
            id=site.id,
            name=site.name
        ),
        inherited=[],
        direct=[],
        effective=[]
    )

    # Get direct permissions on this plan
    result = await db.execute(
        select(ResourcePermission)
        .where(
            ResourcePermission.resource_type == ResourceType.PLAN,
            ResourcePermission.resource_id == plan_id,
            ResourcePermission.effect == Effect.ALLOW,
            (ResourcePermission.expires_at.is_(None) | (ResourcePermission.expires_at > datetime.utcnow()))
        )
    )
    direct_perms = result.scalars().all()

    # Get grantee names for direct permissions
    for perm in direct_perms:
        grantee_name = perm.grantee_id
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
                # Get member count
                member_result = await db.execute(
                    select(ResourcePermission)
                    .where(
                        ResourcePermission.resource_type == ResourceType.GROUP,
                        ResourcePermission.resource_id == group.id,
                        ResourcePermission.permission == Permission.MEMBER,
                        ResourcePermission.effect == Effect.ALLOW
                    )
                )
                member_count = len(member_result.scalars().all())

        response.direct.append(
            PermissionWithGrantee(
                id=perm.id,
                grantee_type=perm.grantee_type,
                grantee_id=perm.grantee_id,
                grantee_name=grantee_name,
                permission=perm.permission,
                effect=perm.effect,
                inherit=perm.inherit,
                fields=perm.fields,
                expires_at=perm.expires_at,
                granted_at=perm.granted_at,
                members=members,
                member_count=member_count
            )
        )

    # Get inherited permissions from parent site (with inherit=True)
    if include_inherited:
        result = await db.execute(
            select(ResourcePermission)
            .where(
                ResourcePermission.resource_type == ResourceType.SITE,
                ResourcePermission.resource_id == site.id,
                ResourcePermission.inherit == True,
                ResourcePermission.effect == Effect.ALLOW,
                (ResourcePermission.expires_at.is_(None) | (ResourcePermission.expires_at > datetime.utcnow()))
            )
        )
        inherited_perms = result.scalars().all()

        for perm in inherited_perms:
            grantee_name = perm.grantee_id
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
                    # Get member count
                    member_result = await db.execute(
                        select(ResourcePermission)
                        .where(
                            ResourcePermission.resource_type == ResourceType.GROUP,
                            ResourcePermission.resource_id == group.id,
                            ResourcePermission.permission == Permission.MEMBER,
                            ResourcePermission.effect == Effect.ALLOW
                        )
                    )
                    member_count = len(member_result.scalars().all())

            response.inherited.append(
                PermissionWithGrantee(
                    id=perm.id,
                    grantee_type=perm.grantee_type,
                    grantee_id=perm.grantee_id,
                    grantee_name=grantee_name,
                    permission=perm.permission,
                    effect=perm.effect,
                    inherit=perm.inherit,
                    fields=perm.fields,
                    expires_at=perm.expires_at,
                    granted_at=perm.granted_at,
                    source=f"site:{site.name}",
                    members=members,
                    member_count=member_count
                )
            )

    # Calculate effective permissions (combined per user)
    if include_effective:
        # Combine all permissions (inherited + direct)
        all_perms = list(inherited_perms if include_inherited else []) + list(direct_perms)

        # Build a map of user -> permissions
        user_perms_map = {}

        for perm in all_perms:
            users_to_add = []
            source = None

            if perm.grantee_type == GranteeType.USER:
                users_to_add.append((perm.grantee_id, "direct"))
            elif perm.grantee_type == GranteeType.GROUP:
                # Get group members
                group_result = await db.execute(
                    select(Group).where(Group.id == perm.grantee_id)
                )
                group = group_result.scalar_one_or_none()
                if group:
                    source = group.name
                    # Get members
                    member_result = await db.execute(
                        select(ResourcePermission)
                        .where(
                            ResourcePermission.resource_type == ResourceType.GROUP,
                            ResourcePermission.resource_id == group.id,
                            ResourcePermission.permission == Permission.MEMBER,
                            ResourcePermission.effect == Effect.ALLOW,
                            ResourcePermission.grantee_type == GranteeType.USER
                        )
                    )
                    member_perms = member_result.scalars().all()
                    for member_perm in member_perms:
                        users_to_add.append((member_perm.grantee_id, source))

            # Add permissions for each user
            for user_id, source_name in users_to_add:
                if user_id not in user_perms_map:
                    user_perms_map[user_id] = {
                        'permissions': set(),
                        'fields': set(),
                        'sources': set(),
                        'has_all_fields': False
                    }

                user_perms_map[user_id]['permissions'].add(perm.permission.value)

                # Track sources
                if source_name:
                    user_perms_map[user_id]['sources'].add(source_name)
                else:
                    user_perms_map[user_id]['sources'].add('direct')

                # Handle fields (None means all fields)
                if perm.fields is None:
                    user_perms_map[user_id]['has_all_fields'] = True
                elif not user_perms_map[user_id]['has_all_fields']:
                    user_perms_map[user_id]['fields'].update(perm.fields)

        # Convert to EffectivePermission objects
        for user_id, perm_data in user_perms_map.items():
            # Get username
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            username = user.username if user else user_id

            # Determine final fields list
            final_fields = None if perm_data['has_all_fields'] else sorted(list(perm_data['fields']))

            response.effective.append(
                EffectivePermission(
                    user_id=user_id,
                    username=username,
                    permissions=sorted(list(perm_data['permissions'])),
                    fields=final_fields,
                    sources=sorted(list(perm_data['sources']))
                )
            )

        # Sort by username
        response.effective.sort(key=lambda x: x.username)

    return response
