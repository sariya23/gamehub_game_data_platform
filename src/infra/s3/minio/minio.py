from io import BytesIO

import structlog
from minio import Minio as MinioClient
from datetime import date

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
    
    def upload_file(self, data: BytesIO, object_name: str, l: int, bucket_name: str):
        try:
            self.__client.put_object(bucket_name=bucket_name, object_name=object_name, data=data, length=l)
            log.info(f"object with name '{object_name}' saved in s3")
        except Exception:
            log.error("cannot save object in s3 with error '{e}'")
    
    @staticmethod
    def build_object_key(source_name: str, object_group: str, load_date: date, filename: str) -> str:
        return f"raw/{source_name}/{object_group}/{load_date.year}/{load_date.month}/{load_date.day}/{filename}"