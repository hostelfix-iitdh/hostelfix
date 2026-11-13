"""Persist the SmartReport once-per-day usage marker."""
from alembic import op
import sqlalchemy as sa

revision = "20261113_0005"
down_revision = "20261113_0004"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("smart_report_last_used_on", sa.Date(), nullable=True))

def downgrade():
    op.drop_column("users", "smart_report_last_used_on")
