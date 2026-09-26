from pathlib import Path

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "0c9582fc18ed_fill_nsi_game_platform_type.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass