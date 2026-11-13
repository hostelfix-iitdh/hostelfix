"""MS5 lifecycle, category targets and audit actor role."""
from alembic import op
import sqlalchemy as sa

revision = "20261113_0004"
down_revision = "20261113_0003"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("categories", sa.Column("resolution_target_hours", sa.Integer(), nullable=False, server_default="168"))
    op.add_column("issues", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.add_column("issue_updates", sa.Column("actor_role", sa.String(length=20), nullable=False, server_default="student"))

def downgrade():
    op.drop_column("issue_updates", "actor_role")
    op.drop_column("issues", "resolved_at")
    op.drop_column("categories", "resolution_target_hours")
