from dataclasses import dataclass

from ...shared import Event

__all__ = ["FileDeleted"]


@dataclass
class FileDeleted(Event):
    id: str
    path: str
