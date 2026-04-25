from typing import Optional

from sqlalchemy import Column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from deps_file.domain.model import ICommandUserRepository, User

from ..tables import user_table
from .user_mapper import UserMapper

__all__ = ["UoWCommandUserRepository"]


class UoWCommandUserRepository(ICommandUserRepository):
    def __init__(self, connection: Session) -> None:
        self._connection = connection

    @property
    def user_columns(self) -> tuple[Column, ...]:
        return (
            user_table.c.user_id,
            user_table.c.first_name,
            user_table.c.last_name,
        )

    def user_of_id(self, user_id: str) -> Optional[User]:
        query = select(*self.user_columns).where(user_table.c.user_id == user_id)

        row = self._connection.execute(query).mappings().first()
        if not row:
            return None
        return UserMapper.from_dict(dict(row))

    def save(self, user: User) -> None:
        insert_query = insert(user_table)
        save_query = insert_query.on_conflict_do_update(
            constraint="user_id",
            set_=dict(insert_query.excluded),
        ).values(**UserMapper.to_dict(user))

        self._connection.execute(save_query)
