from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.permission import PermissionMetadata


class BrokerBase(BaseModel):
    """Base broker schema."""
    name: str
    protocol: str
    host: str
    port: int


class BrokerCreate(BrokerBase):
    """Schema for creating a broker."""
    plan_id: str


class BrokerUpdate(BaseModel):
    """Schema for updating a broker."""
    name: Optional[str] = None
    protocol: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


class BrokerResponse(BrokerBase):
    """Schema for broker response."""
    id: str
    plan_id: str
    created_by: str
    created_at: datetime
    _permissions: Optional[PermissionMetadata] = None

    class Config:
        from_attributes = True
