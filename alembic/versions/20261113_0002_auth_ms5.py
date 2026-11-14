"""MS5 authentication verification flag."""
from alembic import op
import sqlalchemy as sa

revision = "20261113_0002"
down_revision = "20261027_0001"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")))

def downgrade():
    op.drop_column("users", "is_verified")
