from dataclasses import dataclass

from ..shared import Event

__all__ = ["UserCreated"]


@dataclass
class UserCreated(Event):
    id: str
    first_name: str
    last_name: str
