"""add signature_data to signatures

Revision ID: b7d2e9f1c4a3
Revises: 40e630436877
Create Date: 2026-06-18 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7d2e9f1c4a3"
down_revision: str | Sequence[str] | None = "40e630436877"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("signatures", sa.Column("signature_data", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("signatures", "signature_data")
