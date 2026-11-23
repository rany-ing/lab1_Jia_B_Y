"""Add user credentials, roles and refresh sessions."""

import sqlalchemy as sa
from alembic import op

revision = "0003_add_auth"
down_revision = "0002_seed_mock_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255)))
    op.add_column("users", sa.Column("github_id", sa.String(64)))
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_unique_constraint("uq_users_github_id", "users", ["github_id"])

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_table("refresh_sessions")
    op.drop_constraint("uq_users_github_id", "users", type_="unique")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "github_id")
    op.drop_column("users", "password_hash")
