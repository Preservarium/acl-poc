"""Add email, first_name, last_name, and disabled fields to users

Revision ID: 001
Revises:
Create Date: 2025-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new fields to users table."""
    # Add email column
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
    op.create_index('ix_users_email', 'users', ['email'])

    # Add first_name column
    op.add_column('users', sa.Column('first_name', sa.String(255), nullable=True))

    # Add last_name column
    op.add_column('users', sa.Column('last_name', sa.String(255), nullable=True))

    # Add disabled column
    op.add_column('users', sa.Column('disabled', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Remove new fields from users table."""
    op.drop_column('users', 'disabled')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
    op.drop_index('ix_users_email', 'users')
    op.drop_column('users', 'email')
