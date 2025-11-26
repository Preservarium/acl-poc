from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    is_admin: bool = False


class UserUpdate(BaseModel):
    """
    Schema for updating a user's allowed self-update fields.

    Non-admin users can only update these fields on their own account.
    To update other fields, use UserAdminUpdate or have admin privileges.
    """
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)


class UserAdminUpdate(UserUpdate):
    """
    Extended update schema for admins or when updating other users.

    Can modify additional privileged fields beyond what's allowed for self-updates.
    """
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    is_admin: Optional[bool] = None
    disabled: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool
    disabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserBasic(BaseModel):
    """Basic user information for nested responses."""
    id: str
    username: str

    class Config:
        from_attributes = True


class GroupBasic(BaseModel):
    """Basic group information for nested responses."""
    id: str
    name: str

    class Config:
        from_attributes = True


class ResourceWithSource(BaseModel):
    """Resource with permission source information."""
    resource_type: str
    resource_id: str
    resource_name: str
    permission: str
    source: str  # Group name or 'direct'


class DirectPermission(BaseModel):
    """Direct permission information."""
    resource_type: str
    resource_id: str
    resource_name: str
    permission: str
    source: str  # 'creator' or 'direct grant'


class EffectivePermissionsResponse(BaseModel):
    """Complete effective permissions for a user."""
    user: UserBasic
    groups: list[GroupBasic]
    sites_administered: list[ResourceWithSource]
    sites_write: list[ResourceWithSource]
    sites_read: list[ResourceWithSource]
    direct_permissions: list[DirectPermission]
