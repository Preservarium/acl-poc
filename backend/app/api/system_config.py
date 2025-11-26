"""System Configuration API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Hardware, Datatype, Protocol, Parser, Manufacturer, CommunicationMode
from app.models.permission import ResourceType, Permission
from app.schemas import (
    HardwareCreate, HardwareUpdate, HardwareResponse,
    DatatypeCreate, DatatypeUpdate, DatatypeResponse,
    ProtocolCreate, ProtocolUpdate, ProtocolResponse,
    ParserCreate, ParserUpdate, ParserResponse,
    ManufacturerCreate, ManufacturerUpdate, ManufacturerResponse,
    CommunicationModeCreate, CommunicationModeUpdate, CommunicationModeResponse,
)
from app.services.permission_service import PermissionService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/system-config", tags=["system-config"])


# ============================================================
# HARDWARE ENDPOINTS
# ============================================================

@router.get("/hardware", response_model=List[HardwareResponse])
async def list_hardware(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all hardware configurations.

    Readable by any authenticated user (via RESOURCE_DEFAULTS).
    """
    result = await db.execute(select(Hardware))
    hardware_list = result.scalars().all()
    return hardware_list


@router.get("/hardware/{hardware_id}", response_model=HardwareResponse)
async def get_hardware(
    hardware_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific hardware configuration."""
    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id))
    hardware = result.scalar_one_or_none()

    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found"
        )

    return hardware


@router.post("/hardware", response_model=HardwareResponse, status_code=status.HTTP_201_CREATED)
async def create_hardware(
    hardware_data: HardwareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new hardware configuration.

    Requires admin privileges (via RESOURCE_DEFAULTS).
    """
    perm_service = PermissionService(db)

    # Check if user has permission (admin_only via RESOURCE_DEFAULTS)
    # We check on a dummy resource since this is a creation
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create hardware configurations"
        )

    # Check for duplicate name
    result = await db.execute(select(Hardware).where(Hardware.name == hardware_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hardware with this name already exists"
        )

    hardware = Hardware(
        name=hardware_data.name,
        description=hardware_data.description,
    )

    db.add(hardware)
    await db.commit()
    await db.refresh(hardware)

    return hardware


@router.put("/hardware/{hardware_id}", response_model=HardwareResponse)
async def update_hardware(
    hardware_id: str,
    hardware_update: HardwareUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a hardware configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update hardware configurations"
        )

    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id))
    hardware = result.scalar_one_or_none()

    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found"
        )

    if hardware_update.name is not None:
        hardware.name = hardware_update.name
    if hardware_update.description is not None:
        hardware.description = hardware_update.description

    await db.commit()
    await db.refresh(hardware)

    return hardware


@router.delete("/hardware/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hardware(
    hardware_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a hardware configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete hardware configurations"
        )

    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id))
    hardware = result.scalar_one_or_none()

    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware not found"
        )

    await db.delete(hardware)
    await db.commit()


# ============================================================
# DATATYPE ENDPOINTS
# ============================================================

@router.get("/datatypes", response_model=List[DatatypeResponse])
async def list_datatypes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all datatype configurations."""
    result = await db.execute(select(Datatype))
    datatypes = result.scalars().all()
    return datatypes


@router.post("/datatypes", response_model=DatatypeResponse, status_code=status.HTTP_201_CREATED)
async def create_datatype(
    datatype_data: DatatypeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new datatype configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create datatype configurations"
        )

    result = await db.execute(select(Datatype).where(Datatype.name == datatype_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datatype with this name already exists"
        )

    datatype = Datatype(
        name=datatype_data.name,
        description=datatype_data.description,
    )

    db.add(datatype)
    await db.commit()
    await db.refresh(datatype)

    return datatype


@router.put("/datatypes/{datatype_id}", response_model=DatatypeResponse)
async def update_datatype(
    datatype_id: str,
    datatype_update: DatatypeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a datatype configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update datatype configurations"
        )

    result = await db.execute(select(Datatype).where(Datatype.id == datatype_id))
    datatype = result.scalar_one_or_none()

    if not datatype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datatype not found"
        )

    if datatype_update.name is not None:
        datatype.name = datatype_update.name
    if datatype_update.description is not None:
        datatype.description = datatype_update.description

    await db.commit()
    await db.refresh(datatype)

    return datatype


@router.delete("/datatypes/{datatype_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datatype(
    datatype_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a datatype configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete datatype configurations"
        )

    result = await db.execute(select(Datatype).where(Datatype.id == datatype_id))
    datatype = result.scalar_one_or_none()

    if not datatype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datatype not found"
        )

    await db.delete(datatype)
    await db.commit()


# ============================================================
# PROTOCOL ENDPOINTS
# ============================================================

@router.get("/protocols", response_model=List[ProtocolResponse])
async def list_protocols(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all protocol configurations."""
    result = await db.execute(select(Protocol))
    protocols = result.scalars().all()
    return protocols


@router.post("/protocols", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    protocol_data: ProtocolCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new protocol configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create protocol configurations"
        )

    result = await db.execute(select(Protocol).where(Protocol.name == protocol_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Protocol with this name already exists"
        )

    protocol = Protocol(
        name=protocol_data.name,
        description=protocol_data.description,
    )

    db.add(protocol)
    await db.commit()
    await db.refresh(protocol)

    return protocol


@router.put("/protocols/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: str,
    protocol_update: ProtocolUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a protocol configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update protocol configurations"
        )

    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()

    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )

    if protocol_update.name is not None:
        protocol.name = protocol_update.name
    if protocol_update.description is not None:
        protocol.description = protocol_update.description

    await db.commit()
    await db.refresh(protocol)

    return protocol


@router.delete("/protocols/{protocol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protocol(
    protocol_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a protocol configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete protocol configurations"
        )

    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()

    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )

    await db.delete(protocol)
    await db.commit()


# ============================================================
# PARSER ENDPOINTS
# ============================================================

@router.get("/parsers", response_model=List[ParserResponse])
async def list_parsers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all parser configurations."""
    result = await db.execute(select(Parser))
    parsers = result.scalars().all()
    return parsers


@router.post("/parsers", response_model=ParserResponse, status_code=status.HTTP_201_CREATED)
async def create_parser(
    parser_data: ParserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new parser configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create parser configurations"
        )

    result = await db.execute(select(Parser).where(Parser.name == parser_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parser with this name already exists"
        )

    parser = Parser(
        name=parser_data.name,
        description=parser_data.description,
    )

    db.add(parser)
    await db.commit()
    await db.refresh(parser)

    return parser


@router.put("/parsers/{parser_id}", response_model=ParserResponse)
async def update_parser(
    parser_id: str,
    parser_update: ParserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a parser configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update parser configurations"
        )

    result = await db.execute(select(Parser).where(Parser.id == parser_id))
    parser = result.scalar_one_or_none()

    if not parser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parser not found"
        )

    if parser_update.name is not None:
        parser.name = parser_update.name
    if parser_update.description is not None:
        parser.description = parser_update.description

    await db.commit()
    await db.refresh(parser)

    return parser


@router.delete("/parsers/{parser_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parser(
    parser_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a parser configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete parser configurations"
        )

    result = await db.execute(select(Parser).where(Parser.id == parser_id))
    parser = result.scalar_one_or_none()

    if not parser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parser not found"
        )

    await db.delete(parser)
    await db.commit()


# ============================================================
# MANUFACTURER ENDPOINTS
# ============================================================

@router.get("/manufacturers", response_model=List[ManufacturerResponse])
async def list_manufacturers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all manufacturer configurations."""
    result = await db.execute(select(Manufacturer))
    manufacturers = result.scalars().all()
    return manufacturers


@router.post("/manufacturers", response_model=ManufacturerResponse, status_code=status.HTTP_201_CREATED)
async def create_manufacturer(
    manufacturer_data: ManufacturerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new manufacturer configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create manufacturer configurations"
        )

    result = await db.execute(select(Manufacturer).where(Manufacturer.name == manufacturer_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manufacturer with this name already exists"
        )

    manufacturer = Manufacturer(
        name=manufacturer_data.name,
        description=manufacturer_data.description,
    )

    db.add(manufacturer)
    await db.commit()
    await db.refresh(manufacturer)

    return manufacturer


@router.put("/manufacturers/{manufacturer_id}", response_model=ManufacturerResponse)
async def update_manufacturer(
    manufacturer_id: str,
    manufacturer_update: ManufacturerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a manufacturer configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update manufacturer configurations"
        )

    result = await db.execute(select(Manufacturer).where(Manufacturer.id == manufacturer_id))
    manufacturer = result.scalar_one_or_none()

    if not manufacturer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found"
        )

    if manufacturer_update.name is not None:
        manufacturer.name = manufacturer_update.name
    if manufacturer_update.description is not None:
        manufacturer.description = manufacturer_update.description

    await db.commit()
    await db.refresh(manufacturer)

    return manufacturer


@router.delete("/manufacturers/{manufacturer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manufacturer(
    manufacturer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a manufacturer configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete manufacturer configurations"
        )

    result = await db.execute(select(Manufacturer).where(Manufacturer.id == manufacturer_id))
    manufacturer = result.scalar_one_or_none()

    if not manufacturer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found"
        )

    await db.delete(manufacturer)
    await db.commit()


# ============================================================
# COMMUNICATION MODE ENDPOINTS
# ============================================================

@router.get("/communication-modes", response_model=List[CommunicationModeResponse])
async def list_communication_modes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all communication mode configurations."""
    result = await db.execute(select(CommunicationMode))
    modes = result.scalars().all()
    return modes


@router.post("/communication-modes", response_model=CommunicationModeResponse, status_code=status.HTTP_201_CREATED)
async def create_communication_mode(
    mode_data: CommunicationModeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new communication mode configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create communication mode configurations"
        )

    result = await db.execute(select(CommunicationMode).where(CommunicationMode.name == mode_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Communication mode with this name already exists"
        )

    mode = CommunicationMode(
        name=mode_data.name,
        description=mode_data.description,
    )

    db.add(mode)
    await db.commit()
    await db.refresh(mode)

    return mode


@router.put("/communication-modes/{mode_id}", response_model=CommunicationModeResponse)
async def update_communication_mode(
    mode_id: str,
    mode_update: CommunicationModeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a communication mode configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update communication mode configurations"
        )

    result = await db.execute(select(CommunicationMode).where(CommunicationMode.id == mode_id))
    mode = result.scalar_one_or_none()

    if not mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication mode not found"
        )

    if mode_update.name is not None:
        mode.name = mode_update.name
    if mode_update.description is not None:
        mode.description = mode_update.description

    await db.commit()
    await db.refresh(mode)

    return mode


@router.delete("/communication-modes/{mode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_communication_mode(
    mode_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a communication mode configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete communication mode configurations"
        )

    result = await db.execute(select(CommunicationMode).where(CommunicationMode.id == mode_id))
    mode = result.scalar_one_or_none()

    if not mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication mode not found"
        )

    await db.delete(mode)
    await db.commit()
