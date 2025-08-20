"""new table commit

Revision ID: 82a6f8c72524
Revises: f67e8fa3bbce
Create Date: 2025-08-20 14:49:29.143738

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "82a6f8c72524"
down_revision: Union[str, None] = "f67e8fa3bbce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "airportcomments",
        sa.Column("comment_text", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("airport_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        sa.ForeignKeyConstraint(["airport_id"], ["airports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("airportcomments")
