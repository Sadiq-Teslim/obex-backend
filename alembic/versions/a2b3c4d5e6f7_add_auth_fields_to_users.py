"""Add auth tracking fields to users table

Revision ID: a2b3c4d5e6f7
Revises: 3be689a10988
Create Date: 2025-11-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '3be689a10988'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns needed for auth (safe, idempotent SQL).

    We use PostgreSQL's `IF NOT EXISTS` form so this is safe to run
    multiple times and when some columns already exist.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        # Use IF NOT EXISTS for Postgres
        op.execute(
            """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts integer NOT NULL DEFAULT 0;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until timestamp with time zone NULL;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamp with time zone NULL;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip varchar NULL;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT now();
            """
        )
    else:
        # Fallback for SQLite and others: try to add columns, ignore errors
        # SQLite doesn't support IF NOT EXISTS on ALTER COLUMN, so we guard
        try:
            op.add_column('users', sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'))
        except Exception:
            pass
        try:
            op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('users', sa.Column('last_login_ip', sa.String(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
        except Exception:
            pass


def downgrade() -> None:
    """Revert the changes: remove columns if they exist.

    Note: removing columns from production is destructive; use with caution.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        op.execute(
            """
            ALTER TABLE users DROP COLUMN IF EXISTS failed_attempts;
            ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
            ALTER TABLE users DROP COLUMN IF EXISTS last_login_at;
            ALTER TABLE users DROP COLUMN IF EXISTS last_login_ip;
            ALTER TABLE users DROP COLUMN IF EXISTS created_at;
            """
        )
    else:
        # SQLite: drop columns not directly supported; keep simple attempts
        # Some environments may not allow drop - in that case, skip.
        try:
            op.drop_column('users', 'failed_attempts')
        except Exception:
            pass
        try:
            op.drop_column('users', 'locked_until')
        except Exception:
            pass
        try:
            op.drop_column('users', 'last_login_at')
        except Exception:
            pass
        try:
            op.drop_column('users', 'last_login_ip')
        except Exception:
            pass
        try:
            op.drop_column('users', 'created_at')
        except Exception:
            pass
