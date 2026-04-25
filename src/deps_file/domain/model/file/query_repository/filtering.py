from dataclasses import dataclass
from datetime import datetime

__all__ = ["FileFiltering"]


@dataclass
class FileFiltering:
    tenant_id: str
    name: str | None = None
    state: list[str] | None = None
    labels: list[str] | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None
    reference_available: bool | None = None
    entity_name: str | None = None
