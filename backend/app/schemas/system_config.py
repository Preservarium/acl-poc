from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Hardware Schemas
class HardwareBase(BaseModel):
    """Base hardware schema."""
    name: str
    description: Optional[str] = None


class HardwareCreate(HardwareBase):
    """Schema for creating hardware."""
    pass


class HardwareUpdate(BaseModel):
    """Schema for updating hardware."""
    name: Optional[str] = None
    description: Optional[str] = None


class HardwareResponse(HardwareBase):
    """Schema for hardware response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Datatype Schemas
class DatatypeBase(BaseModel):
    """Base datatype schema."""
    name: str
    description: Optional[str] = None


class DatatypeCreate(DatatypeBase):
    """Schema for creating datatype."""
    pass


class DatatypeUpdate(BaseModel):
    """Schema for updating datatype."""
    name: Optional[str] = None
    description: Optional[str] = None


class DatatypeResponse(DatatypeBase):
    """Schema for datatype response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Protocol Schemas
class ProtocolBase(BaseModel):
    """Base protocol schema."""
    name: str
    description: Optional[str] = None


class ProtocolCreate(ProtocolBase):
    """Schema for creating protocol."""
    pass


class ProtocolUpdate(BaseModel):
    """Schema for updating protocol."""
    name: Optional[str] = None
    description: Optional[str] = None


class ProtocolResponse(ProtocolBase):
    """Schema for protocol response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Parser Schemas
class ParserBase(BaseModel):
    """Base parser schema."""
    name: str
    description: Optional[str] = None


class ParserCreate(ParserBase):
    """Schema for creating parser."""
    pass


class ParserUpdate(BaseModel):
    """Schema for updating parser."""
    name: Optional[str] = None
    description: Optional[str] = None


class ParserResponse(ParserBase):
    """Schema for parser response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Manufacturer Schemas
class ManufacturerBase(BaseModel):
    """Base manufacturer schema."""
    name: str
    description: Optional[str] = None


class ManufacturerCreate(ManufacturerBase):
    """Schema for creating manufacturer."""
    pass


class ManufacturerUpdate(BaseModel):
    """Schema for updating manufacturer."""
    name: Optional[str] = None
    description: Optional[str] = None


class ManufacturerResponse(ManufacturerBase):
    """Schema for manufacturer response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Communication Mode Schemas
class CommunicationModeBase(BaseModel):
    """Base communication mode schema."""
    name: str
    description: Optional[str] = None


class CommunicationModeCreate(CommunicationModeBase):
    """Schema for creating communication mode."""
    pass


class CommunicationModeUpdate(BaseModel):
    """Schema for updating communication mode."""
    name: Optional[str] = None
    description: Optional[str] = None


class CommunicationModeResponse(CommunicationModeBase):
    """Schema for communication mode response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
