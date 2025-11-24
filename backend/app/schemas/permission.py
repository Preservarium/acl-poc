from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class GranteeType(str, Enum):
    """Grantee type enum."""
    USER = "user"
    GROUP = "group"


class ResourceType(str, Enum):
    """Resource type enum."""
    SITE = "site"
    PLAN = "plan"
    SENSOR = "sensor"


class PermissionEnum(str, Enum):
    """Permission enum."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    MANAGE = "manage"


class Effect(str, Enum):
    """Effect enum."""
    ALLOW = "allow"
    DENY = "deny"


class PermissionCreate(BaseModel):
    """Schema for creating a permission."""
    grantee_type: GranteeType
    grantee_id: str
    resource_type: ResourceType
    resource_id: str
    permission: PermissionEnum
    effect: Effect = Effect.ALLOW
    inherit: bool = True


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    id: str
    grantee_type: GranteeType
    grantee_id: str
    grantee_name: Optional[str] = None
    resource_type: ResourceType
    resource_id: str
    resource_name: Optional[str] = None
    permission: PermissionEnum
    effect: Effect
    inherit: bool
    granted_by: Optional[str] = None
    granted_at: datetime

    class Config:
        from_attributes = True


class PermissionCheck(BaseModel):
    """Schema for a single permission check."""
    resource_type: ResourceType
    resource_id: str
    permission: PermissionEnum


class PermissionCheckRequest(BaseModel):
    """Schema for bulk permission check request."""
    checks: List[PermissionCheck]


class PermissionCheckResult(BaseModel):
    """Schema for a single permission check result."""
    resource_type: ResourceType
    resource_id: str
    permission: PermissionEnum
    allowed: bool


class PermissionCheckResponse(BaseModel):
    """Schema for bulk permission check response."""
    results: List[PermissionCheckResult]
