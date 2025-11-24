from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    groups = relationship(
        "Group",
        secondary="group_users",
        back_populates="users",
        lazy="selectin"
    )
    permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.grantee_id",
        primaryjoin="and_(User.id==ResourcePermission.grantee_id, ResourcePermission.grantee_type=='user')",
        back_populates="user_grantee",
        lazy="selectin"
    )
    granted_permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.granted_by",
        back_populates="granter",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"
