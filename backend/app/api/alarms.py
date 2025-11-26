"""Alarms API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Alarm, Sensor
from app.models.permission import ResourceType, Permission
from app.schemas import AlarmCreate, AlarmUpdate, AlarmResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("", response_model=List[AlarmResponse])
async def list_alarms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all alarms the current user has access to.

    Returns alarms where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all alarms
    result = await db.execute(select(Alarm))
    all_alarms = result.scalars().all()

    # Filter alarms based on permissions
    accessible_alarms = []
    for alarm in all_alarms:
        has_access = await perm_service.check(
            current_user,
            ResourceType.ALARM,
            alarm.id,
            Permission.READ
        )
        if has_access:
            accessible_alarms.append(alarm)

    return accessible_alarms


@router.get("/sensor/{sensor_id}", response_model=List[AlarmResponse])
async def list_alarms_for_sensor(
    sensor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all alarms for a specific sensor.
    Path: /api/alarms/sensor/{sensor_id}

    Requires 'read' permission on the sensor.
    """
    perm_service = PermissionService(db)

    # Check permission on sensor
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SENSOR,
        sensor_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this sensor"
        )

    # Get alarms for sensor
    result = await db.execute(
        select(Alarm).where(Alarm.sensor_id == sensor_id)
    )
    alarms = result.scalars().all()

    # Filter based on alarm-level permissions
    accessible_alarms = []
    for alarm in alarms:
        has_access = await perm_service.check(
            current_user,
            ResourceType.ALARM,
            alarm.id,
            Permission.READ
        )
        if has_access:
            accessible_alarms.append(alarm)

    return accessible_alarms


@router.post("", response_model=AlarmResponse, status_code=status.HTTP_201_CREATED)
async def create_alarm(
    alarm_data: AlarmCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new alarm.

    Requires 'create' permission on the parent sensor.
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Check if sensor exists
    result = await db.execute(select(Sensor).where(Sensor.id == alarm_data.sensor_id))
    sensor = result.scalar_one_or_none()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )

    # Check 'create' permission on parent sensor
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SENSOR,
        alarm_data.sensor_id,
        Permission.CREATE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create alarms for this sensor"
        )

    # Create the alarm
    alarm = Alarm(
        name=alarm_data.name,
        threshold=alarm_data.threshold,
        condition=alarm_data.condition,
        active=alarm_data.active,
        sensor_id=alarm_data.sensor_id,
        created_by=current_user.id,
    )

    db.add(alarm)
    await db.commit()
    await db.refresh(alarm)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.ALARM,
        resource_id=alarm.id,
    )

    return alarm


@router.get("/{alarm_id}", response_model=AlarmResponse)
async def get_alarm(
    alarm_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific alarm.

    Requires 'read' permission on the alarm.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALARM,
        alarm_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this alarm"
        )

    # Get alarm
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )

    # Convert to response model
    response = AlarmResponse.model_validate(alarm)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.ALARM,
            alarm_id
        )

    return response


@router.put("/{alarm_id}", response_model=AlarmResponse)
async def update_alarm(
    alarm_id: str,
    alarm_update: AlarmUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an alarm.

    Requires 'write' permission on the alarm.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALARM,
        alarm_id,
        Permission.WRITE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this alarm"
        )

    # Get alarm
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )

    # Update fields
    if alarm_update.name is not None:
        alarm.name = alarm_update.name
    if alarm_update.threshold is not None:
        alarm.threshold = alarm_update.threshold
    if alarm_update.condition is not None:
        alarm.condition = alarm_update.condition
    if alarm_update.active is not None:
        alarm.active = alarm_update.active

    await db.commit()
    await db.refresh(alarm)

    return alarm


@router.delete("/{alarm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm(
    alarm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an alarm.

    Requires 'delete' permission on the alarm.
    Cascades to all alerts associated with the alarm.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALARM,
        alarm_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this alarm"
        )

    # Get alarm
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )

    # Delete alarm (cascades to alerts)
    await db.delete(alarm)
    await db.commit()
