from io import BytesIO

from PIL import Image

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
    "image/x-icon": ".ico",
}

def get_image_mime(data: bytes) -> str:
    with Image.open(BytesIO(data)) as image:
        return Image.MIME[image.format]