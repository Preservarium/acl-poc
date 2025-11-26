"""Sensors API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Sensor, Plan
from app.models.permission import ResourceType, Permission
from app.schemas import SensorCreate, SensorResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("", response_model=List[SensorResponse])
async def list_sensors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all sensors the current user has access to.

    Returns sensors where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all sensors
    result = await db.execute(select(Sensor))
    all_sensors = result.scalars().all()

    # Filter sensors based on permissions
    accessible_sensors = []
    for sensor in all_sensors:
        has_access = await perm_service.check(
            current_user,
            ResourceType.SENSOR,
            sensor.id,
            Permission.READ
        )
        if has_access:
            accessible_sensors.append(sensor)

    return accessible_sensors


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor(
    sensor_data: SensorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new sensor.

    Requires 'create' permission on the parent plan.
    Auto-grants 'manage' permission to the creator with inheritance.
    """
    perm_service = PermissionService(db)

    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == sensor_data.plan_id))
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
        sensor_data.plan_id,
        Permission.CREATE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create sensors in this plan"
        )

    # Create the sensor
    sensor = Sensor(
        name=sensor_data.name,
        plan_id=sensor_data.plan_id,
        created_by=current_user.id,
    )

    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)

    # Auto-grant manage permission to creator
    await perm_service.auto_grant_manage(
        creator_id=current_user.id,
        resource_type=ResourceType.SENSOR,
        resource_id=sensor.id,
    )

    return sensor


@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific sensor.

    Requires 'read' permission on the sensor.
    """
    perm_service = PermissionService(db)

    # Check permission
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

    # Get sensor
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = result.scalar_one_or_none()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )

    # Convert to response model
    response = SensorResponse.model_validate(sensor)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.SENSOR,
            sensor_id
        )

    return response


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(
    sensor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a sensor.

    Requires 'delete' permission on the sensor.
    """
    # Get sensor first (to check existence and get name)
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = result.scalar_one_or_none()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found"
        )

    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.SENSOR,
        sensor_id,
        Permission.DELETE
    )

    if not has_permission:
        # Use the new helper function to provide detailed permission info
        from app.core.dependencies import raise_permission_denied
        await raise_permission_denied(
            db,
            current_user,
            ResourceType.SENSOR.value,
            sensor_id,
            Permission.DELETE.value,
            sensor.name
        )

    # Delete sensor
    await db.delete(sensor)
    await db.commit()
