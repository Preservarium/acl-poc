from datetime import datetime
from typing import List
from sqlalchemy import Column, String, Boolean, DateTime, select, and_, or_
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # DEPRECATED: This relationship uses the old group_users table which has been migrated
    # to resource_permissions. Use get_groups() method instead.
    # This is kept for backward compatibility during transition period.
    # groups = relationship(
    #     "Group",
    #     secondary="group_users",
    #     back_populates="users",
    #     lazy="selectin"
    # )

    # Permissions where this user is the grantee
    permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.grantee_id",
        primaryjoin="and_(User.id==ResourcePermission.grantee_id, ResourcePermission.grantee_type=='user')",
        back_populates="user_grantee",
        lazy="selectin"
    )

    # Permissions granted by this user
    granted_permissions = relationship(
        "ResourcePermission",
        foreign_keys="ResourcePermission.granted_by",
        back_populates="granter",
        lazy="selectin"
    )

    # Audit logs where this user is the actor
    audit_logs_as_actor = relationship(
        "AuditLog",
        foreign_keys="AuditLog.actor_id",
        back_populates="actor"
    )

    # Audit logs where this user is the target
    audit_logs_as_target = relationship(
        "AuditLog",
        foreign_keys="AuditLog.target_user_id",
        back_populates="target_user"
    )

    async def get_groups(self, db_session) -> List["Group"]:
        """
        Get all groups this user is a member of via resource_permissions.

        Group membership is represented as 'member' permission on group resources.

        Args:
            db_session: SQLAlchemy async session

        Returns:
            List of Group objects this user is a member of
        """
        from app.models.group import Group
        from app.models.permission import ResourcePermission, GranteeType, ResourceType, Permission, Effect

        # Get group IDs where user has member permission
        result = await db_session.execute(
            select(ResourcePermission.resource_id)
            .where(
                and_(
                    ResourcePermission.grantee_type == GranteeType.USER,
                    ResourcePermission.grantee_id == self.id,
                    ResourcePermission.resource_type == ResourceType.GROUP,
                    ResourcePermission.permission == Permission.MEMBER,
                    ResourcePermission.effect == Effect.ALLOW,
                    or_(
                        ResourcePermission.expires_at.is_(None),
                        ResourcePermission.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        group_ids = [row[0] for row in result.all()]

        # Get group objects
        if not group_ids:
            return []

        groups_result = await db_session.execute(
            select(Group).where(Group.id.in_(group_ids)).order_by(Group.name)
        )
        return list(groups_result.scalars().all())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"
