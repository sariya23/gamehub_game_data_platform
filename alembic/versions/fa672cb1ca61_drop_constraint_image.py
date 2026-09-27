from pathlib import Path

from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "fa672cb1ca61_drop_constraint_image.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass