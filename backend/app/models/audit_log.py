from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.database import Base


class AuditAction(str, enum.Enum):
    """Audit log action types."""
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_EXPIRED = "permission_expired"


class AuditLog(Base):
    """Audit log model for tracking permission changes."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)

    # Actor (who performed the action)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Target user (if permission was granted/revoked for a user)
    target_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Target group (if permission was granted/revoked for a group)
    target_group_id = Column(String(36), ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)

    # Resource affected
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)

    # Permission details
    permission = Column(String(50), nullable=True)

    # Additional details (JSON)
    details = Column(JSON, nullable=True)

    # Relationships
    actor = relationship("User", foreign_keys=[actor_id], back_populates="audit_logs_as_actor")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="audit_logs_as_target")
    target_group = relationship("Group", foreign_keys=[target_group_id], back_populates="audit_logs")

    def __repr__(self):
        return (
            f"<AuditLog("
            f"action={self.action}, "
            f"actor_id={self.actor_id}, "
            f"timestamp={self.timestamp})>"
        )
