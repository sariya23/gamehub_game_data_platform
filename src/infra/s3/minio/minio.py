import structlog
from minio import Minio as MinioClient

log = structlog.get_logger()

class Minio:
    def __init__(self, client: MinioClient):
        self.__client = client
    
    def create_or_ignore_bucket(self, bucket_name: str):
        found = self.__client.bucket_exists(bucket_name)
        if not found:
            self.__client.make_bucket(bucket_name)
            log.info(f"bucket {bucket_name} created")
        else:
            log.info(f"bucket {bucket_name} already exists")