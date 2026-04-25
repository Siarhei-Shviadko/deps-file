from dataclasses import dataclass

from ...shared import Event

__all__ = ["FileProcessed"]


@dataclass
class FileProcessed(Event):
    id: str
    status: str
    purpose: str
    metadata: dict | None
    error_message: str | None
