"""baseline

Revision ID: 88244613a42f
Revises:
Create Date: 2026-06-13 17:23:47.387127

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "88244613a42f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
