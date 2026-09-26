from pathlib import Path

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "8e46dc99a2fe_nsi_game_platform.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass