import structlog

from config import load_config
from src.infra.s3.minio.create import create_minio

log = structlog.get_logger()
config = load_config(".env.local")
log.info(f"start in '{config.env.type}' env")

m = create_minio(config=config.s3)
