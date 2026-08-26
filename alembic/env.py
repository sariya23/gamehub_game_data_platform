import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def get_required_env(name: str, env_path: Path) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set in env file: {env_path}")
    return value


def configure_database_url() -> None:
    """Build Alembic's database URL from values in the supplied env file."""
    env_file = context.get_x_argument(as_dictionary=True).get("env_file")
    if not env_file:
        raise RuntimeError(
            "Path to the env file is required. "
            "Run: alembic -x env_file=path/to/.env upgrade head"
        )

    env_path = Path(env_file).expanduser()
    if not env_path.is_file():
        raise FileNotFoundError(f"Env file does not exist: {env_path}")

    load_dotenv(env_path, override=True)


    database_url = URL.create(
        drivername=os.getenv("DATABASE__DRIVER", "postgresql+psycopg"),
        username=get_required_env("DATABASE__USER", env_path),
        password=get_required_env("DATABASE__PASSWORD", env_path),
        host=get_required_env("DATABASE__HOST", env_path),
        port=int(get_required_env("DATABASE__PORT", env_path)),
        database=get_required_env("DATABASE__NAME", env_path),
        query={
            "sslmode": get_required_env("DATABASE__SSL_MODE", env_path),
        },
    ).render_as_string(hide_password=False)

    # ConfigParser treats '%' as interpolation syntax. URLs commonly contain
    # percent-encoded characters, so they must be escaped before assignment.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


configure_database_url()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
