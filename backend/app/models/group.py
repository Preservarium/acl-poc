from datetime import datetime
from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base

# Association table for many-to-many relationship between groups and users
group_users = Table(
    "group_users",
    Base.metadata,
    Column("group_id", String(36), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Group(Base):
    """Group model."""

    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary="group_users",
        back_populates="groups",
        lazy="selectin"
    )
    permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.grantee_id",
        primaryjoin="and_(Group.id==ResourcePermission.grantee_id, ResourcePermission.grantee_type=='group')",
        back_populates="group_grantee",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name})>"
