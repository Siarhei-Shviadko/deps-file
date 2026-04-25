import logging

from deps_file.domain.exceptions import UserNotFound
from deps_file.domain.model import IQueryUserRepository, UserInfo

__all__ = ["QueryUserService"]


class QueryUserService:
    def __init__(
        self,
        query_user_repository: IQueryUserRepository,
    ) -> None:
        self._query_user_repository = query_user_repository

        self._logger = logging.getLogger(self.__class__.__name__)

    def find_user(self, id_: str) -> UserInfo:
        if (user := self._query_user_repository.find_user(id_)) is None:
            raise UserNotFound(id_)

        self._logger.info("User with id `%s` found.", id_)

        return user
