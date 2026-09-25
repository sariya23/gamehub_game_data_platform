import sys

import structlog
from minio import Minio as MinioClient

from config import S3Config
from src.infra.s3.minio.minio import Minio

log = structlog.get_logger(__name__)

def create_minio(config: S3Config) -> Minio:
    client = MinioClient(access_key=config.root_user, secret_key=config.root_password.get_secret_value(), 
                 endpoint=f"{config.host}:{config.api_port}", secure=config.secure)
    try:
        client.list_buckets()
        log.info("s3.client_ready", host=config.host, port=config.api_port)
        c = Minio(client=client)
        return c
    except Exception as e:
        log.exception("s3.client_failed", operation="connect", host=config.host, port=config.api_port, error_type=type(e).__name__)
        sys.exit()
        
        