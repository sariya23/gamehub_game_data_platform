import httpx


def download_image(url: str) -> bytes:
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    return response.content