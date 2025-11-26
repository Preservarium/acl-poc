from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.permission import PermissionMetadata


class AlertBase(BaseModel):
    """Base alert schema."""
    message: str
    severity: str  # info, warning, critical
    triggered_at: datetime
    acknowledged: bool = False


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    alarm_id: str


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    acknowledged: Optional[bool] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: str
    alarm_id: str
    created_at: datetime
    _permissions: Optional[PermissionMetadata] = None

    class Config:
        from_attributes = True
