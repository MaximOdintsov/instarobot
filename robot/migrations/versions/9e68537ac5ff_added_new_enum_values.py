"""added new enum values

Revision ID: 9e68537ac5ff
Revises: e32b1ff977e5
Create Date: 2025-03-22 16:03:57.189288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e68537ac5ff'
down_revision: Union[str, None] = 'adc0d866105f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'RAP_ARTIST'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'BLOGGER'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'DANCER'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'DESIGNER'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'DJ'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE 'PHOTOGRAPHER'")


def downgrade():
    raise NotImplementedError("Откат миграции для enum типов не поддерживается.")
