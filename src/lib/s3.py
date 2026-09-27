from io import BytesIO

from infra.s3.minio.minio import Minio
from models.dto.game_image import GameImageDTO


def upload_image(
    minio: Minio,
    image: bytes,
    source_url: str,
    object_key: str,
    screenshot: bool,
    bucket_name: str
) -> GameImageDTO:
    minio.upload_file(
        BytesIO(image),
        object_key,
        len(image),
        bucket_name,
    )

    return GameImageDTO(
        source_url=source_url,
        bucket=bucket_name,
        object_key=object_key,
        screenshot=screenshot,
    )