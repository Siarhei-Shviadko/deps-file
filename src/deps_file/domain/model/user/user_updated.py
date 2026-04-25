from dataclasses import dataclass

from ..shared import Event

__all__ = ["UserUpdated"]


@dataclass
class UserUpdated(Event):
    id: str
    first_name: str
    last_name: str
