from pathlib import Path

from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "9db837b521cc_rempve_game_source.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass