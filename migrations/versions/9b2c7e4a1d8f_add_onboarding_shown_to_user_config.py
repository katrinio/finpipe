"""add onboarding_shown to user_config

Revision ID: 9b2c7e4a1d8f
Revises: a63372892e58
Create Date: 2026-06-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9b2c7e4a1d8f"
down_revision: str | Sequence[str] | None = "a63372892e58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_config",
        sa.Column("onboarding_shown", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
    )


def downgrade() -> None:
    op.drop_column("user_config", "onboarding_shown")
