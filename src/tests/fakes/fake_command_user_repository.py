import logging
from typing import Optional

from deps_file.domain.model import ICommandUserRepository, User

__all__ = ["FakeCommandUserRepository"]


class FakeCommandUserRepository(ICommandUserRepository):
    def __init__(self, users: Optional[list[User]] = None) -> None:
        self._db: dict[str, User] = {user.id(): user for user in users} if users else {}

        self._logger = logging.getLogger(self.__class__.__name__)

    def user_of_id(self, user_id: str) -> Optional[User]:
        return self._db.get(user_id)

    def save(self, user: User) -> None:
        self._db[user.id()] = user
