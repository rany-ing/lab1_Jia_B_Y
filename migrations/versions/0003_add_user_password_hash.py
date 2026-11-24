"""Add nullable password hashes for account login."""

import sqlalchemy as sa
from alembic import op

revision = "0003_add_user_password_hash"
down_revision = "0002_seed_mock_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
