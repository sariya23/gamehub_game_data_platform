from pathlib import Path

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "f1804d750300_nsi_game_rating_source.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass