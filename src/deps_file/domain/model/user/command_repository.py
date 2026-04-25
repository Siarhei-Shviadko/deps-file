from typing import Optional, Protocol

from .user import User

__all__ = ["ICommandUserRepository"]


class ICommandUserRepository(Protocol):
    def user_of_id(self, user_id: str) -> Optional[User]:
        pass

    def save(self, user: User) -> None:
        pass
