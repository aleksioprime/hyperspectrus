"""add description to chromophore

Revision ID: b51beec5b08a
Revises: 1c0107a4e55a
Create Date: 2025-07-08 18:06:47.050261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b51beec5b08a'
down_revision: Union[str, None] = '1c0107a4e55a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chromophores', sa.Column('description', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chromophores', 'description')
    # ### end Alembic commands ###
