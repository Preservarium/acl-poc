"""Alerts API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Alert, Alarm
from app.models.permission import ResourceType, Permission
from app.schemas import AlertUpdate, AlertResponse
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all alerts the current user has access to.

    Returns alerts where the user has at least 'read' permission.
    """
    perm_service = PermissionService(db)

    # Get all alerts
    result = await db.execute(select(Alert))
    all_alerts = result.scalars().all()

    # Filter alerts based on permissions
    accessible_alerts = []
    for alert in all_alerts:
        has_access = await perm_service.check(
            current_user,
            ResourceType.ALERT,
            alert.id,
            Permission.READ
        )
        if has_access:
            accessible_alerts.append(alert)

    return accessible_alerts


@router.get("/alarm/{alarm_id}", response_model=List[AlertResponse])
async def list_alerts_for_alarm(
    alarm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all alerts for a specific alarm.
    Path: /api/alerts/alarm/{alarm_id}

    Requires 'read' permission on the alarm.
    """
    perm_service = PermissionService(db)

    # Check permission on alarm
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

    # Get alerts for alarm
    result = await db.execute(
        select(Alert).where(Alert.alarm_id == alarm_id)
    )
    alerts = result.scalars().all()

    # Filter based on alert-level permissions
    accessible_alerts = []
    for alert in alerts:
        has_access = await perm_service.check(
            current_user,
            ResourceType.ALERT,
            alert.id,
            Permission.READ
        )
        if has_access:
            accessible_alerts.append(alert)

    return accessible_alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    include_permissions: bool = Query(False, description="Include permission metadata in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific alert.

    Requires 'read' permission on the alert.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALERT,
        alert_id,
        Permission.READ
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this alert"
        )

    # Get alert
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Convert to response model
    response = AlertResponse.model_validate(alert)

    # Add permission metadata if requested
    if include_permissions:
        response._permissions = await perm_service.get_permission_metadata(
            current_user,
            ResourceType.ALERT,
            alert_id
        )

    return response


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an alert (typically to acknowledge it).

    Requires 'write' permission on the alert.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALERT,
        alert_id,
        Permission.WRITE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this alert"
        )

    # Get alert
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Update fields (typically just acknowledged)
    if alert_update.acknowledged is not None:
        alert.acknowledged = alert_update.acknowledged

    await db.commit()
    await db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an alert.

    Requires 'delete' permission on the alert.
    """
    perm_service = PermissionService(db)

    # Check permission
    has_permission = await perm_service.check(
        current_user,
        ResourceType.ALERT,
        alert_id,
        Permission.DELETE
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this alert"
        )

    # Get alert
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Delete alert
    await db.delete(alert)
    await db.commit()
