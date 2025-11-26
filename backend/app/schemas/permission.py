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
    GROUP = "group"
    USER = "user"
    SITE = "site"
    PLAN = "plan"
    SENSOR = "sensor"
    BROKER = "broker"
    ALARM = "alarm"
    ALERT = "alert"
    DASHBOARD = "dashboard"


class PermissionEnum(str, Enum):
    """Permission enum."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    MANAGE = "manage"
    MEMBER = "member"


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
    fields: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


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
    fields: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
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


class PermissionMetadata(BaseModel):
    """Schema for permission metadata to include in API responses."""
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_create: bool = False
    can_manage: bool = False
    writable_fields: Optional[List[str]] = None


class PermissionWithGrantee(BaseModel):
    """Schema for permission with full grantee details."""
    id: str
    grantee_type: GranteeType
    grantee_id: str
    grantee_name: str
    permission: PermissionEnum
    effect: Effect
    inherit: bool
    fields: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    granted_at: datetime
    granted_by_name: Optional[str] = None
    source: Optional[str] = None  # For inherited permissions, shows the parent resource
    # For groups only:
    members: Optional[List[str]] = None
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class EffectivePermission(BaseModel):
    """Schema for effective permission showing combined access per user."""
    user_id: str
    username: str
    permissions: List[str]  # e.g., ['read', 'write']
    fields: Optional[List[str]] = None  # Combined fields, None means all
    sources: List[str]  # e.g., ['Factory 1 Admins', 'direct']


class ParentInfo(BaseModel):
    """Schema for parent resource information."""
    type: str  # 'site', 'plan', etc.
    id: str
    name: str


class PlanPermissionsResponse(BaseModel):
    """Schema for plan permissions response with inherited/direct/effective sections."""
    parent: ParentInfo
    inherited: List[PermissionWithGrantee]
    direct: List[PermissionWithGrantee]
    effective: List[EffectivePermission]


class MatrixGrantee(BaseModel):
    """Schema for a grantee in the permission matrix."""
    grantee_id: str
    grantee_name: str
    grantee_type: GranteeType


class MatrixPermissionInfo(BaseModel):
    """Schema for permission info in matrix cell."""
    allowed: bool
    inherited: bool = False
    has_field_restrictions: bool = False
    fields: Optional[List[str]] = None
    source: Optional[str] = None  # Parent resource if inherited


class MatrixRow(BaseModel):
    """Schema for a row in the permission matrix."""
    grantee: MatrixGrantee
    permissions: dict  # Maps permission type ('read', 'write', etc.) to MatrixPermissionInfo


class PermissionMatrixResponse(BaseModel):
    """Schema for permission matrix response."""
    resource_type: str
    resource_id: str
    resource_name: str
    grantees: List[MatrixRow]


class ExpiringPermissionResponse(BaseModel):
    """Schema for expiring permission response."""
    id: str
    grantee_type: GranteeType
    grantee_id: str
    grantee_name: Optional[str] = None
    resource_type: ResourceType
    resource_id: str
    resource_name: Optional[str] = None
    permission: PermissionEnum
    effect: Effect
    expires_at: datetime
    granted_at: datetime
    granted_by: Optional[str] = None
    days_until_expiry: int

    class Config:
        from_attributes = True
