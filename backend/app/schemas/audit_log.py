from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum


class AuditAction(str, Enum):
    """Audit log action types."""
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_EXPIRED = "permission_expired"


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    action: AuditAction
    actor_id: Optional[str] = None
    target_user_id: Optional[str] = None
    target_group_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    permission: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: str
    timestamp: datetime
    action: AuditAction
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    target_user_id: Optional[str] = None
    target_user_name: Optional[str] = None
    target_group_id: Optional[str] = None
    target_group_name: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    permission: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
