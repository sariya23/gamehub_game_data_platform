import structlog
from minio import Minio as MinioClient
from io import BytesIO

log = structlog.get_logger()

class Minio:
    def __init__(self, client: MinioClient, bucket_name: str):
        self.__client = client
        self.bucket_name = bucket_name
    
    def create_or_ignore_bucket(self):
        found = self.__client.bucket_exists(self.bucket_name)
        if not found:
            self.__client.make_bucket(self.bucket_name)
            log.info(f"bucket {self.bucket_name} created")
        else:
            log.info(f"bucket {self.bucket_name} already exists")
    
    def upload_file(self, data: BytesIO, object_name: str, l: int):
        try:
            self.__client.put_object(bucket_name=self.bucket_name, object_name=object_name, data=data, length=l)
            log.info(f"object with name '{object_name}' saved in s3")
        except Exception as e:
            log.error("cannot save object in s3 with error '{e}'")