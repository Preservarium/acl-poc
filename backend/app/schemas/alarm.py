from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.permission import PermissionMetadata


class AlarmBase(BaseModel):
    """Base alarm schema."""
    name: str
    threshold: float
    condition: str  # gt, lt, eq, gte, lte
    active: bool = True


class AlarmCreate(AlarmBase):
    """Schema for creating an alarm."""
    sensor_id: str


class AlarmUpdate(BaseModel):
    """Schema for updating an alarm."""
    name: Optional[str] = None
    threshold: Optional[float] = None
    condition: Optional[str] = None
    active: Optional[bool] = None


class AlarmResponse(AlarmBase):
    """Schema for alarm response."""
    id: str
    sensor_id: str
    created_by: str
    created_at: datetime
    _permissions: Optional[PermissionMetadata] = None

    class Config:
        from_attributes = True
