from dataclasses import dataclass

from ...shared import Event

__all__ = ["FileStateUpdated"]


@dataclass
class FileStateUpdated(Event):
    file_id: str
    state: str
    metadata: dict
    error_message: str | None = None
