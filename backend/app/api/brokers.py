"""Brokers API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Broker, Plan
from app.models.permission import ResourceType, Permission
from app.schemas import BrokerCreate, BrokerUpdate, BrokerResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/brokers", tags=["brokers"])


@router.get("", response_model=List[BrokerResponse])
async def list_brokers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all brokers the current user has access to.

    Returns brokers where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all brokers
    result = await db.execute(select(Broker))
    all_brokers = result.scalars().all()

    # Filter brokers based on permissions
    accessible_brokers = []
    for broker in all_brokers:
        has_access = await perm_service.check(
            current_user,
            ResourceType.BROKER,
            broker.id,
            Permission.READ
        )
        if has_access:
            accessible_brokers.append(broker)

    return accessible_brokers


@router.get("/plan/{plan_id}", response_model=List[BrokerResponse])
async def list_brokers_for_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all brokers for a specific plan.
    Path: /api/brokers/plan/{plan_id}

    Requires 'read' permission on the plan.
    """
    perm_service = PermissionService(db)

    # Check permission on plan
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

    # Get brokers for plan
    result = await db.execute(
        select(Broker).where(Broker.plan_id == plan_id)
    )
    brokers = result.scalars().all()

    # Filter based on broker-level permissions
    accessible_brokers = []
    for broker in brokers:
        has_access = await perm_service.check(
            current_user,
            ResourceType.BROKER,
            broker.id,
            Permission.READ
        )
        if has_access:
            accessible_brokers.append(broker)

    return accessible_brokers


@router.post("", response_model=BrokerResponse, status_code=status.HTTP_201_CREATED)
async def create_broker(
    broker_data: BrokerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new broker.

    Requires 'create' permission on the parent plan.
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == broker_data.plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    # Check 'create' permission on parent plan
    has_permission = await perm_service.check(
        current_user,
        ResourceType.PLAN,
        broker_data.plan_id,
        Permission.CREATE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create brokers in this plan"
        )

    # Create the broker
    broker = Broker(
        name=broker_data.name,
        protocol=broker_data.protocol,
        host=broker_data.host,
        port=broker_data.port,
        plan_id=broker_data.plan_id,
        created_by=current_user.id,
    )

    db.add(broker)
    await db.commit()
    await db.refresh(broker)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.BROKER,
        resource_id=broker.id,
    )

    return broker


@router.get("/{broker_id}", response_model=BrokerResponse)
async def get_broker(
    broker_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific broker.

    Requires 'read' permission on the broker.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.BROKER,
        broker_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this broker"
        )

    # Get broker
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()

    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )

    # Convert to response model
    response = BrokerResponse.model_validate(broker)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.BROKER,
            broker_id
        )

    return response


@router.put("/{broker_id}", response_model=BrokerResponse)
async def update_broker(
    broker_id: str,
    broker_update: BrokerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a broker.

    Requires 'write' permission on the broker.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.BROKER,
        broker_id,
        Permission.WRITE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this broker"
        )

    # Get broker
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()

    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )

    # Update fields
    if broker_update.name is not None:
        broker.name = broker_update.name
    if broker_update.protocol is not None:
        broker.protocol = broker_update.protocol
    if broker_update.host is not None:
        broker.host = broker_update.host
    if broker_update.port is not None:
        broker.port = broker_update.port

    await db.commit()
    await db.refresh(broker)

    return broker


@router.delete("/{broker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker(
    broker_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a broker.

    Requires 'delete' permission on the broker.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.BROKER,
        broker_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this broker"
        )

    # Get broker
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()

    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )

    # Delete broker
    await db.delete(broker)
    await db.commit()
