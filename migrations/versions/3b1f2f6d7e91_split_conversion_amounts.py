"""split conversion order amounts

Revision ID: 3b1f2f6d7e91
Revises: e05c13c6dd2a
Create Date: 2026-06-14 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3b1f2f6d7e91"
down_revision: str | Sequence[str] | None = "e05c13c6dd2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_config", sa.Column("bank_received_amount_eur", sa.Float(), nullable=True))
    op.add_column("user_config", sa.Column("conversion_amount_eur", sa.Float(), nullable=True))

    op.execute(
        """
        UPDATE user_config
        SET bank_received_amount_eur = received_amount_eur,
            conversion_amount_eur = COALESCE(exchange_amount_eur, received_amount_eur)
        """
    )


def downgrade() -> None:
    op.drop_column("user_config", "conversion_amount_eur")
    op.drop_column("user_config", "bank_received_amount_eur")
