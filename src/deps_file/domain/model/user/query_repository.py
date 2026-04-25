from typing import Optional, Protocol

from .user_info import UserInfo

__all__ = ["IQueryUserRepository"]


class IQueryUserRepository(Protocol):
    def find_user(self, id_: str) -> Optional[UserInfo]:
        pass
