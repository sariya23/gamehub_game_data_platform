from collections.abc import Iterator
from datetime import date
from io import BytesIO

import structlog
from minio import Minio as MinioClient
from minio.error import S3Error

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
            self.__client.put_object(
                bucket_name=bucket_name, object_name=object_name, data=data, length=l
            )
            log.info(f"object with name '{object_name}' saved in s3")
        except S3Error as error:
            log.error("cannot save object in s3", error=str(error))

    def get_files(self, bucket_name: str, file_group: str) -> Iterator[bytes]:
        for object_info in self.__client.list_objects(
            bucket_name,
            prefix=file_group,
        ):
            if object_info.is_dir:
                continue
            response = self.__client.get_object(bucket_name, object_info.object_name)
            try:
                yield response.read()
            except Exception as e:
                log.error("cannot read from bucket with error '{e}'")
            finally:
                response.close()
                response.release_conn()

    @staticmethod
    def build_object_key(
        prefix: str, source_name: str, object_group: str, load_date: date, filename: str
    ) -> str:
        return f"raw/{source_name}/{object_group}/{load_date.year}/{load_date.month}/{load_date.day}/{filename}"
