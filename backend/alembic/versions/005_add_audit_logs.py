"""Add audit logs table

Revision ID: 005
Revises: 004
Create Date: 2025-11-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('action', sa.Enum(
            'permission_granted',
            'permission_revoked',
            'permission_denied',
            'permission_expired',
            name='auditaction'
        ), nullable=False),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_group_id', sa.String(36), sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('permission', sa.String(50), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
    )

    # Create indexes for better query performance
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'])
    op.create_index('ix_audit_logs_target_user_id', 'audit_logs', ['target_user_id'])
    op.create_index('ix_audit_logs_target_group_id', 'audit_logs', ['target_group_id'])


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index('ix_audit_logs_target_group_id', 'audit_logs')
    op.drop_index('ix_audit_logs_target_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_actor_id', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_timestamp', 'audit_logs')
    op.drop_table('audit_logs')
