from collections.abc import Iterator
from datetime import date
from io import BytesIO

import structlog
from minio import Minio as MinioClient
from minio.error import S3Error

log = structlog.get_logger(__name__)


class Minio:
    def __init__(self, client: MinioClient):
        self.__client = client

    def create_or_ignore_bucket(self, bucket_name: str):
        found = self.__client.bucket_exists(bucket_name)
        if not found:
            self.__client.make_bucket(bucket_name)
            log.info("s3.bucket_created", bucket=bucket_name)
        else:
            log.info("s3.bucket_exists", bucket=bucket_name)

    def upload_file(self, data: BytesIO, object_name: str, l: int, bucket_name: str):
        try:
            self.__client.put_object(
                bucket_name=bucket_name, object_name=object_name, data=data, length=l
            )
            log.info("s3.object_uploaded", bucket=bucket_name, object_key=object_name, size_bytes=l)
        except S3Error as error:
            log.exception("s3.upload_failed", operation="put_object", bucket=bucket_name, object_key=object_name, size_bytes=l, error_type=type(error).__name__)

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
            except Exception:
                log.exception("s3.read_failed", operation="read_object", bucket=bucket_name, prefix=file_group, object_key=object_info.object_name)
            finally:
                response.close()
                response.release_conn()

    @staticmethod
    def build_object_key(
        prefix: str, source_name: str, object_group: str, load_date: date, filename: str
    ) -> str:
        return (
            f"{prefix}/{source_name}/{object_group}/"
            f"{load_date.year}/{load_date.month}/{load_date.day}/"
            f"{filename}"
        )
