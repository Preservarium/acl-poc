from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# Site schemas
class SiteBase(BaseModel):
    """Base site schema."""
    name: str = Field(..., min_length=1, max_length=255)


class SiteCreate(SiteBase):
    """Schema for creating a site."""
    pass


class SiteResponse(SiteBase):
    """Schema for site response."""
    id: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Plan schemas
class PlanBase(BaseModel):
    """Base plan schema."""
    name: str = Field(..., min_length=1, max_length=255)


class PlanCreate(PlanBase):
    """Schema for creating a plan."""
    site_id: str


class PlanResponse(PlanBase):
    """Schema for plan response."""
    id: str
    site_id: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Sensor schemas
class SensorBase(BaseModel):
    """Base sensor schema."""
    name: str = Field(..., min_length=1, max_length=255)


class SensorCreate(SensorBase):
    """Schema for creating a sensor."""
    plan_id: str


class SensorResponse(SensorBase):
    """Schema for sensor response."""
    id: str
    plan_id: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
