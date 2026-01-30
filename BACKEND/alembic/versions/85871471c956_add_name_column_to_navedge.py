"""Add name column to NavEdge

Revision ID: 85871471c956
Revises: 7afd3510b18f
Create Date: 2026-01-30 11:01:05.358084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '85871471c956'
down_revision: Union[str, Sequence[str], None] = '7afd3510b18f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('nav_edges', sa.Column('name', sa.String(), nullable=True, comment='Road name (e.g., NH-27)'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('nav_edges', 'name')
