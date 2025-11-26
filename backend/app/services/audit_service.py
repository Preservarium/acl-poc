"""Audit logging service for tracking permission changes."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.audit_log import AuditLog, AuditAction


class AuditService:
    """Service for managing audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_permission_granted(
        self,
        actor_id: Optional[str],
        target_user_id: Optional[str],
        target_group_id: Optional[str],
        resource_type: str,
        resource_id: str,
        permission: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a permission granted event.

        Args:
            actor_id: ID of user who granted the permission
            target_user_id: ID of user who received the permission (if grantee is user)
            target_group_id: ID of group that received the permission (if grantee is group)
            resource_type: Type of resource
            resource_id: ID of resource
            permission: Permission type (read, write, etc.)
            details: Additional details (e.g., effect, inherit, fields)

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            action=AuditAction.PERMISSION_GRANTED,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_group_id=target_group_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            details=details or {}
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def log_permission_revoked(
        self,
        actor_id: Optional[str],
        target_user_id: Optional[str],
        target_group_id: Optional[str],
        resource_type: str,
        resource_id: str,
        permission: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a permission revoked event.

        Args:
            actor_id: ID of user who revoked the permission
            target_user_id: ID of user whose permission was revoked (if grantee is user)
            target_group_id: ID of group whose permission was revoked (if grantee is group)
            resource_type: Type of resource
            resource_id: ID of resource
            permission: Permission type (read, write, etc.)
            details: Additional details

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            action=AuditAction.PERMISSION_REVOKED,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_group_id=target_group_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            details=details or {}
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def log_permission_denied(
        self,
        actor_id: Optional[str],
        target_user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        permission: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a permission denied event (when access is attempted but denied).

        Args:
            actor_id: ID of user who was denied access
            target_user_id: Same as actor_id (for consistency)
            resource_type: Type of resource
            resource_id: ID of resource
            permission: Permission type that was denied
            details: Additional details (e.g., reason for denial)

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            action=AuditAction.PERMISSION_DENIED,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_group_id=None,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            details=details or {}
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def log_permission_expired(
        self,
        target_user_id: Optional[str],
        target_group_id: Optional[str],
        resource_type: str,
        resource_id: str,
        permission: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a permission expired event (when a time-limited permission expires).

        Args:
            target_user_id: ID of user whose permission expired (if grantee is user)
            target_group_id: ID of group whose permission expired (if grantee is group)
            resource_type: Type of resource
            resource_id: ID of resource
            permission: Permission type that expired
            details: Additional details (e.g., expiration date)

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            action=AuditAction.PERMISSION_EXPIRED,
            actor_id=None,  # No actor for system-triggered events
            target_user_id=target_user_id,
            target_group_id=target_group_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            details=details or {}
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log
