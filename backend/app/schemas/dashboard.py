from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import json
from app.schemas.permission import PermissionMetadata


class DashboardBase(BaseModel):
    """Base dashboard schema."""
    name: str
    config: Dict[str, Any] = {}

    @field_validator('config', mode='before')
    @classmethod
    def parse_config(cls, v):
        """Parse config from JSON string if needed (SQLite returns JSON as string)."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}


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
