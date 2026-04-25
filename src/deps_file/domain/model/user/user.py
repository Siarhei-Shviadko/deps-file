from typing import Optional

from ..shared import EntityId, Event, Guard, ImmutableCheck, LengthCheck
from .user_updated import UserUpdated

__all__ = ["User"]


class User:
    id = Guard[EntityId](EntityId, ImmutableCheck())
    first_name = Guard[str](str, LengthCheck())
    last_name = Guard[str](str, LengthCheck())

    def __init__(
        self,
        id_: str,
        first_name: str,
        last_name: str,
        *,
        events: Optional[list[Event]] = None,
    ) -> None:
        self.id = EntityId(id_)
        self.first_name = first_name
        self.last_name = last_name

        self.events = events or []

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __repr__(self) -> str:
        return "\n".join(
            (
                f"<class '{self.__class__.__name__}':",
                f"{self.id =},",
                f"{self.first_name =},",
                f"{self.last_name =}>",
            ),
        )

    def update(self, first_name: str, last_name: str) -> None:
        self.first_name = first_name
        self.last_name = last_name

        self.events.append(
            UserUpdated(
                id=self.id(),
                first_name=first_name,
                last_name=last_name,
            ),
        )
