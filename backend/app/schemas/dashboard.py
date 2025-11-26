from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.permission import PermissionMetadata


class DashboardBase(BaseModel):
    """Base dashboard schema."""
    name: str
    config: Dict[str, Any] = {}


class DashboardCreate(DashboardBase):
    """Schema for creating a dashboard."""
    pass


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard."""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class DashboardResponse(DashboardBase):
    """Schema for dashboard response."""
    id: str
    created_by: str
    created_at: datetime
    _permissions: Optional[PermissionMetadata] = None

    class Config:
        from_attributes = True
