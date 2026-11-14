"""Add optional asset to issues."""
from alembic import op
import sqlalchemy as sa
revision="20261113_0003"
down_revision="20261113_0002"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("issues", sa.Column("asset_id", sa.Integer(), nullable=True))
    op.create_index("ix_issues_asset_id", "issues", ["asset_id"])
    op.create_foreign_key("fk_issues_asset_id_assets", "issues", "assets", ["asset_id"], ["id"], ondelete="SET NULL")
def downgrade():
    op.drop_constraint("fk_issues_asset_id_assets", "issues", type_="foreignkey")
    op.drop_index("ix_issues_asset_id", table_name="issues")
    op.drop_column("issues", "asset_id")
