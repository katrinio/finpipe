"""drop conversion_order_path from pending_bank_reply

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("pending_bank_reply", "conversion_order_path")


def downgrade() -> None:
    op.add_column("pending_bank_reply", sa.Column("conversion_order_path", sa.String(), nullable=False, server_default=""))
