from pathlib import Path

from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "7b5076a3813c_reorg_image_table.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass