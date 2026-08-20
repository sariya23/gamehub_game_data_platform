from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RawBatch(BaseModel):
    source: str
    resource: str
    extracted_at: datetime
    records: list[dict[str, Any]]
