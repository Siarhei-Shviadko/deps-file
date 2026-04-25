from typing import Optional

from sqlalchemy import Column, select

from deps_file.domain.model import IQueryUserRepository, UserInfo
from deps_file.extras import DatabaseSession

from ..tables import user_table
from .user_info_mapper import UserInfoMapper

__all__ = ["QueryUserRepository"]


class QueryUserRepository(IQueryUserRepository):
    def __init__(self, database: DatabaseSession) -> None:
        self._db = database

    @property
    def user_columns(self) -> tuple[Column, ...]:
        return (
            user_table.c.user_id,
            user_table.c.first_name,
            user_table.c.last_name,
        )

    def find_user(self, id_: str) -> Optional[UserInfo]:
        query = select(*self.user_columns).where(
            user_table.c.user_id == id_,
        )

        with self._db.connection() as conn:
            row = conn.execute(query).mappings().first()
            if not row:
                return None
            return UserInfoMapper.from_row(dict(row))
