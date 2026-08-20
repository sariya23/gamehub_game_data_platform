from dataclasses import dataclass


@dataclass
class SourceResponse:
    source: str
    data: dict