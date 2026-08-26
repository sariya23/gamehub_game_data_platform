from pathlib import Path

from alembic import op


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "5b70eae24a9f_init_project_schema_up.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass