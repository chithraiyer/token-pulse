"""seed reference rows: demo teams and the reserved unattributed member

Revision ID: 0002_seed_reference
Revises: 0001_initial
Create Date: 2026-09-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from tokenpulse.db.models import UNATTRIBUTED_MEMBER_ID

revision = "0002_seed_reference"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_TEAM = sa.table("team", sa.column("id", sa.String), sa.column("name", sa.String))
_MEMBER = sa.table(
    "member",
    sa.column("id", sa.String),
    sa.column("display_name", sa.String),
    sa.column("team_id", sa.String),
    sa.column("is_unattributed", sa.Boolean),
)

_TEAMS = [
    {"id": "platform", "name": "Platform"},
    {"id": "product", "name": "Product"},
]


def upgrade() -> None:
    op.bulk_insert(_TEAM, _TEAMS)
    op.bulk_insert(
        _MEMBER,
        [
            {
                "id": UNATTRIBUTED_MEMBER_ID,
                "display_name": "Unattributed",
                "team_id": "platform",
                "is_unattributed": True,
            }
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM member WHERE id = :mid"), {"mid": UNATTRIBUTED_MEMBER_ID})
    bind.execute(sa.text("DELETE FROM team WHERE id IN ('platform', 'product')"))
