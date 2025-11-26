from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.database import Base


class GranteeType(str, enum.Enum):
    """Type of grantee (user or group)."""
    USER = "user"
    GROUP = "group"


class ResourceType(str, enum.Enum):
    """Type of resource."""
    GROUP = "group"
    USER = "user"
    SITE = "site"
    PLAN = "plan"
    SENSOR = "sensor"
    BROKER = "broker"
    ALARM = "alarm"
    ALERT = "alert"
    DASHBOARD = "dashboard"
    HARDWARE = "hardware"
    DATATYPE = "datatype"
    PROTOCOL = "protocol"
    PARSER = "parser"
    MANUFACTURER = "manufacturer"
    COMMUNICATION_MODE = "communication_mode"


class Permission(str, enum.Enum):
    """Permission types."""
    MEMBER = "member"  # Group membership only
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    MANAGE = "manage"


class Effect(str, enum.Enum):
    """Permission effect (allow or deny)."""
    ALLOW = "allow"
    DENY = "deny"


class ResourcePermission(Base):
    """Resource permission model - core ACL table."""

    __tablename__ = "resource_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Grantee (who gets the permission)
    grantee_type = Column(SQLEnum(GranteeType), nullable=False)
    grantee_id = Column(String(36), nullable=False, index=True)

    # Resource (what the permission applies to)
    resource_type = Column(SQLEnum(ResourceType), nullable=False, index=True)
    resource_id = Column(String(36), nullable=False, index=True)

    # Permission details
    permission = Column(SQLEnum(Permission), nullable=False)
    effect = Column(SQLEnum(Effect), default=Effect.ALLOW, nullable=False)
    inherit = Column(Boolean, default=True, nullable=False)
    fields = Column(JSON, nullable=True)  # List of field names or null for all
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    granted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_permissions")
    user_grantee = relationship(
        "User",
        foreign_keys=[grantee_id],
        primaryjoin="and_(ResourcePermission.grantee_id==User.id, ResourcePermission.grantee_type=='user')",
        back_populates="permissions",
        viewonly=True
    )
    group_grantee = relationship(
        "Group",
        foreign_keys=[grantee_id],
        primaryjoin="and_(ResourcePermission.grantee_id==Group.id, ResourcePermission.grantee_type=='group')",
        back_populates="permissions",
        viewonly=True
    )

    def __repr__(self):
        return (
            f"<ResourcePermission("
            f"grantee={self.grantee_type}:{self.grantee_id}, "
            f"resource={self.resource_type}:{self.resource_id}, "
            f"permission={self.permission}, "
            f"effect={self.effect}, "
            f"inherit={self.inherit})>"
        )
