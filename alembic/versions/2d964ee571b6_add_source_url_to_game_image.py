from pathlib import Path

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).parent / "sql"


def upgrade() -> None:
    sql = (SQL_DIR / "2d964ee571b6_add_source_url_to_game_image_up.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    pass