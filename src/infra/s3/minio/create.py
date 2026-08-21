import sys

import structlog
from minio import Minio as MinioClient
from src.infra.s3.minio.minio import Minio

from config import S3Config

log = structlog.get_logger()

def create_minio(config: S3Config) -> Minio:
    client = MinioClient(access_key=config.root_user, secret_key=config.root_password.get_secret_value(), 
                 endpoint=f"{config.host}:{config.api_port}", secure=config.secure)
    try:
        client.list_buckets()
        log.info("minio client created")
        c = Minio(client=client)
        return c
    except Exception as e:
        log.error(f"cannot create minio client with error '{e}'")
        sys.exit()
        
        