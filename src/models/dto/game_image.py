from dataclasses import dataclass


@dataclass
class GameImageDTO:
    source_url: str
    bucket: str
    object_key: str
    screenshot: bool