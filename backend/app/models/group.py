from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, select, and_, or_
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Group(Base):
    """Group model."""

    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    # DEPRECATED: This relationship uses the old group_users table which has been migrated
    # to resource_permissions. Use get_members() method instead.
    # This is kept for backward compatibility during transition period.
    # users = relationship(
    #     "User",
    #     secondary="group_users",
    #     back_populates="groups",
    #     lazy="selectin"
    # )

    # Permissions where this group is the grantee
    permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.grantee_id",
        primaryjoin="and_(Group.id==ResourcePermission.grantee_id, ResourcePermission.grantee_type=='group')",
        back_populates="group_grantee",
        lazy="selectin",
        overlaps="permissions"
    )

    # Audit logs where this group is the target
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.target_group_id",
        back_populates="target_group"
    )

    async def get_members(self, db_session) -> List["User"]:
        """
        Get all members of this group via resource_permissions.

        Members are users who have 'member' permission on this group.

        Args:
            db_session: SQLAlchemy async session

        Returns:
            List of User objects who are members of this group
        """
        from app.models.user import User
        from app.models.permission import ResourcePermission, GranteeType, ResourceType, Permission, Effect

        # Get user IDs with member permission
        result = await db_session.execute(
            select(ResourcePermission.grantee_id)
            .where(
                and_(
                    ResourcePermission.grantee_type == GranteeType.USER,
                    ResourcePermission.resource_type == ResourceType.GROUP,
                    ResourcePermission.resource_id == self.id,
                    ResourcePermission.permission == Permission.MEMBER,
                    ResourcePermission.effect == Effect.ALLOW,
                    or_(
                        ResourcePermission.expires_at.is_(None),
                        ResourcePermission.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        user_ids = [row[0] for row in result.all()]

        # Get user objects
        if not user_ids:
            return []

        users_result = await db_session.execute(
            select(User).where(User.id.in_(user_ids)).order_by(User.username)
        )
        return list(users_result.scalars().all())

    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name})>"
