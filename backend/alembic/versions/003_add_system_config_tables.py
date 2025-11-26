"""Add system config tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-26 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add system configuration tables."""

    # Hardware table
    op.create_table(
        'hardware',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_hardware_name', 'hardware', ['name'])

    # Datatypes table
    op.create_table(
        'datatypes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_datatypes_name', 'datatypes', ['name'])

    # Protocols table
    op.create_table(
        'protocols',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_protocols_name', 'protocols', ['name'])

    # Parsers table
    op.create_table(
        'parsers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_parsers_name', 'parsers', ['name'])

    # Manufacturers table
    op.create_table(
        'manufacturers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_manufacturers_name', 'manufacturers', ['name'])

    # Communication Modes table
    op.create_table(
        'communication_modes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_communication_modes_name', 'communication_modes', ['name'])


def downgrade() -> None:
    """Remove system configuration tables."""
    op.drop_index('ix_communication_modes_name', 'communication_modes')
    op.drop_table('communication_modes')

    op.drop_index('ix_manufacturers_name', 'manufacturers')
    op.drop_table('manufacturers')

    op.drop_index('ix_parsers_name', 'parsers')
    op.drop_table('parsers')

    op.drop_index('ix_protocols_name', 'protocols')
    op.drop_table('protocols')

    op.drop_index('ix_datatypes_name', 'datatypes')
    op.drop_table('datatypes')

    op.drop_index('ix_hardware_name', 'hardware')
    op.drop_table('hardware')
