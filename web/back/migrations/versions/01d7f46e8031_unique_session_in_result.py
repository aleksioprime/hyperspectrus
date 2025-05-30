"""unique session in result

Revision ID: 01d7f46e8031
Revises: ad0482761009
Create Date: 2025-03-26 16:38:02.974801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01d7f46e8031'
down_revision: Union[str, None] = 'ad0482761009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'results', ['session_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'results', type_='unique')
    # ### end Alembic commands ###
