"""Audit logs API endpoints."""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.database import get_db
from app.models import User, Group, AuditLog
from app.models.audit_log import AuditAction
from app.schemas import AuditLogResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


async def get_actor_name(db: AsyncSession, actor_id: Optional[str]) -> Optional[str]:
    """Get the name of the actor (user who performed the action)."""
    if not actor_id:
        return None
    result = await db.execute(select(User).where(User.id == actor_id))
    user = result.scalar_one_or_none()
    return user.username if user else None


async def get_target_user_name(db: AsyncSession, user_id: Optional[str]) -> Optional[str]:
    """Get the name of the target user."""
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.username if user else None


async def get_target_group_name(db: AsyncSession, group_id: Optional[str]) -> Optional[str]:
    """Get the name of the target group."""
    if not group_id:
        return None
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    return group.name if group else None


async def get_resource_name(db: AsyncSession, resource_type: Optional[str], resource_id: Optional[str]) -> Optional[str]:
    """Get the name of a resource."""
    if not resource_type or not resource_id:
        return None

    from app.models import Site, Plan, Sensor, Broker, Alarm, Alert, Dashboard

    if resource_type == "site":
        result = await db.execute(select(Site).where(Site.id == resource_id))
        site = result.scalar_one_or_none()
        return site.name if site else None
    elif resource_type == "plan":
        result = await db.execute(select(Plan).where(Plan.id == resource_id))
        plan = result.scalar_one_or_none()
        return plan.name if plan else None
    elif resource_type == "sensor":
        result = await db.execute(select(Sensor).where(Sensor.id == resource_id))
        sensor = result.scalar_one_or_none()
        return sensor.name if sensor else None
    elif resource_type == "broker":
        result = await db.execute(select(Broker).where(Broker.id == resource_id))
        broker = result.scalar_one_or_none()
        return broker.name if broker else None
    elif resource_type == "alarm":
        result = await db.execute(select(Alarm).where(Alarm.id == resource_id))
        alarm = result.scalar_one_or_none()
        return alarm.name if alarm else None
    elif resource_type == "alert":
        result = await db.execute(select(Alert).where(Alert.id == resource_id))
        alert = result.scalar_one_or_none()
        return f"Alert {alert.id[:8]}" if alert else None
    elif resource_type == "dashboard":
        result = await db.execute(select(Dashboard).where(Dashboard.id == resource_id))
        dashboard = result.scalar_one_or_none()
        return dashboard.name if dashboard else None
    elif resource_type == "group":
        result = await db.execute(select(Group).where(Group.id == resource_id))
        group = result.scalar_one_or_none()
        return group.name if group else None
    elif resource_type == "user":
        result = await db.execute(select(User).where(User.id == resource_id))
        user = result.scalar_one_or_none()
        return user.username if user else None

    return None


async def enrich_audit_log(db: AsyncSession, log: AuditLog) -> AuditLogResponse:
    """Enrich an audit log with names."""
    actor_name = await get_actor_name(db, log.actor_id)
    target_user_name = await get_target_user_name(db, log.target_user_id)
    target_group_name = await get_target_group_name(db, log.target_group_id)
    resource_name = await get_resource_name(db, log.resource_type, log.resource_id)

    return AuditLogResponse(
        id=log.id,
        timestamp=log.timestamp,
        action=log.action,
        actor_id=log.actor_id,
        actor_name=actor_name,
        target_user_id=log.target_user_id,
        target_user_name=target_user_name,
        target_group_id=log.target_group_id,
        target_group_name=target_group_name,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        resource_name=resource_name,
        permission=log.permission,
        details=log.details,
    )


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user (actor or target)"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter logs until this date"),
    days: Optional[int] = Query(7, description="Show logs from last N days (default: 7)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List audit logs with optional filters.

    Filters:
    - action: permission_granted, permission_revoked, permission_denied, permission_expired
    - user_id: Filter by actor or target user
    - date_from/date_to: Date range filter
    - days: Shortcut to filter last N days (default: 7)
    - page/page_size: Pagination

    Requires admin access.
    """
    # Only admins can view audit logs
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )

    # Build query
    conditions = []

    # Action filter
    if action:
        try:
            action_enum = AuditAction(action)
            conditions.append(AuditLog.action == action_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action type: {action}"
            )

    # User filter (actor or target)
    if user_id:
        conditions.append(
            or_(
                AuditLog.actor_id == user_id,
                AuditLog.target_user_id == user_id
            )
        )

    # Date range filter
    if date_from:
        conditions.append(AuditLog.timestamp >= date_from)
    elif days:
        # Default to last N days
        date_from = datetime.utcnow() - timedelta(days=days)
        conditions.append(AuditLog.timestamp >= date_from)

    if date_to:
        conditions.append(AuditLog.timestamp <= date_to)

    # Build query with filters
    query = select(AuditLog)
    if conditions:
        query = query.where(and_(*conditions))

    # Order by timestamp descending (most recent first)
    query = query.order_by(desc(AuditLog.timestamp))

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    # Enrich with names
    enriched = []
    for log in logs:
        enriched.append(await enrich_audit_log(db, log))

    return enriched


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific audit log entry by ID.

    Requires admin access.
    """
    # Only admins can view audit logs
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )

    # Get log
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    # Enrich and return
    return await enrich_audit_log(db, log)
