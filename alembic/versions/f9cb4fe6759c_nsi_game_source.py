from pathlib import Path

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "f9cb4fe6759c_nsi_game_source.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass