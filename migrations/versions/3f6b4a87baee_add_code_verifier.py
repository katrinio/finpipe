"""add code verifier

Revision ID: 3f6b4a87baee
Revises: 9b2c7e4a1d8f
Create Date: 2026-06-17 15:08:18.206742

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f6b4a87baee"
down_revision: str | Sequence[str] | None = "9b2c7e4a1d8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.add_column(
        "oauth_sessions",
        sa.Column("code_verifier", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("oauth_sessions", "code_verifier")
