"""Migrate group membership from group_users to resource_permissions

Revision ID: 002
Revises: 001
Create Date: 2025-11-26 13:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate group membership from group_users association table to
    resource_permissions using 'member' permission.
    """
    # Create a temporary table reference for reading existing data
    connection = op.get_bind()

    # Check if group_users table exists (SQLite compatible)
    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='group_users'")
    )
    table_exists = result.fetchone() is not None

    if table_exists:
        # Get all existing group memberships
        memberships = connection.execute(
            sa.text("SELECT group_id, user_id FROM group_users")
        ).fetchall()

        # Insert memberships into resource_permissions as 'member' permissions
        if memberships:
            print(f"Migrating {len(memberships)} group memberships to resource_permissions...")

            for membership in memberships:
                group_id = membership[0]
                user_id = membership[1]

                # Check if this membership permission already exists
                existing = connection.execute(
                    sa.text("""
                        SELECT id FROM resource_permissions
                        WHERE grantee_type = 'user'
                        AND grantee_id = :user_id
                        AND resource_type = 'group'
                        AND resource_id = :group_id
                        AND permission = 'member'
                    """),
                    {"user_id": user_id, "group_id": group_id}
                ).fetchone()

                if not existing:
                    # Generate UUID for the permission
                    import uuid
                    perm_id = str(uuid.uuid4())

                    # Insert the member permission
                    connection.execute(
                        sa.text("""
                            INSERT INTO resource_permissions
                            (id, grantee_type, grantee_id, resource_type, resource_id,
                             permission, effect, inherit, granted_at)
                            VALUES
                            (:id, 'user', :user_id, 'group', :group_id,
                             'member', 'allow', FALSE, :granted_at)
                        """),
                        {
                            "id": perm_id,
                            "user_id": user_id,
                            "group_id": group_id,
                            "granted_at": datetime.utcnow()
                        }
                    )
                    print(f"  Migrated membership: user {user_id} -> group {group_id}")
                else:
                    print(f"  Skipped existing membership: user {user_id} -> group {group_id}")

        # Drop the group_users association table
        print("Dropping group_users table...")
        op.drop_table('group_users')
        print("Migration completed successfully!")
    else:
        print("group_users table does not exist, skipping migration.")


def downgrade() -> None:
    """
    Recreate group_users table and restore memberships from resource_permissions.
    """
    # Recreate the group_users association table
    op.create_table(
        'group_users',
        sa.Column('group_id', sa.String(36), sa.ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    )

    # Get connection
    connection = op.get_bind()

    # Get all member permissions
    memberships = connection.execute(
        sa.text("""
            SELECT grantee_id as user_id, resource_id as group_id
            FROM resource_permissions
            WHERE grantee_type = 'user'
            AND resource_type = 'group'
            AND permission = 'member'
            AND effect = 'allow'
        """)
    ).fetchall()

    # Insert into group_users
    if memberships:
        print(f"Restoring {len(memberships)} group memberships to group_users table...")
        for membership in memberships:
            user_id = membership[0]
            group_id = membership[1]

            connection.execute(
                sa.text("INSERT INTO group_users (group_id, user_id) VALUES (:group_id, :user_id)"),
                {"group_id": group_id, "user_id": user_id}
            )
            print(f"  Restored membership: user {user_id} -> group {group_id}")

    # Delete member permissions from resource_permissions
    connection.execute(
        sa.text("""
            DELETE FROM resource_permissions
            WHERE grantee_type = 'user'
            AND resource_type = 'group'
            AND permission = 'member'
        """)
    )

    print("Downgrade completed successfully!")
