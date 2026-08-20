import sys

import structlog
from minio import Minio

from config import S3Config

log = structlog.get_logger()

def create_minio(config: S3Config) -> Minio:
    client = Minio(access_key=config.root_user, secret_key=config.root_password.get_secret_value(), 
                 endpoint=f"{config.host}:{config.api_port}", secure=config.secure)
    try:
        client.list_buckets()
        log.info("minio client created")
        return client
    except Exception as e:
        log.error(f"cannot create minio client with error '{e}'")
        sys.exit()
        
        