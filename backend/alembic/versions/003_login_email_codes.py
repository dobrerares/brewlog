"""login email codes

Revision ID: 003
Revises: 002
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_email_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_email_codes_user_id", "login_email_codes", ["user_id"], unique=False)
    op.create_index("ix_login_email_codes_expires_at", "login_email_codes", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_login_email_codes_expires_at", table_name="login_email_codes")
    op.drop_index("ix_login_email_codes_user_id", table_name="login_email_codes")
    op.drop_table("login_email_codes")
