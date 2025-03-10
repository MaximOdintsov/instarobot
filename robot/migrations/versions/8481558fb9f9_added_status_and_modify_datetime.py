"""added status and modify_datetime

Revision ID: 8481558fb9f9
Revises: 18f0adf86f18
Create Date: 2025-01-08 13:49:03.256262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8481558fb9f9'
down_revision: Union[str, None] = '18f0adf86f18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('accounts', sa.Column('modify_datetime', sa.DateTime(), nullable=True))
    op.add_column('accounts', sa.Column('status', sa.Enum('PARSING', 'PREDICTING', 'FAILED', 'READY', 'SENT', 'VALIDATED', name='status_enum'), server_default='PARSING', nullable=False))
    # ### end Alembic commands ###
    op.execute('UPDATE accounts SET modify_datetime = CURRENT_TIMESTAMP WHERE modify_datetime IS NULL')


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('accounts', 'status')
    op.drop_column('accounts', 'modify_datetime')
    # ### end Alembic commands ###
