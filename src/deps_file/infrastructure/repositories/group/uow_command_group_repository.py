from typing import Optional

from sqlalchemy.orm import Session

from deps_file.domain.model.group import Group, ICommandGroupRepository

from .mappers import GroupMapper
from .query_factory import QueryGroupFactory

__all__ = ["UoWCommandGroupRepository"]


class UoWCommandGroupRepository(ICommandGroupRepository):
    def __init__(self, connection: Session) -> None:
        self._connection = connection
        self._query_factory = QueryGroupFactory()

    def group_of_id(self, id_: str, tenant_id: str) -> Optional[Group]:
        query = self._query_factory.find_group(id_, tenant_id)

        row = self._connection.execute(query).mappings().first()

        if not row:
            return None

        return GroupMapper.from_dict(dict(row))

    def save(self, group: Group) -> None:
        save_query = self._query_factory.save_group(group)

        self._connection.execute(save_query)

    def delete(self, group: Group) -> None:
        self.save(group)

    def sync_groups(self, groups: list[Group]) -> None:
        if not groups:
            return

        sync_query = self._query_factory.save_group_fields(groups)
        self._connection.execute(sync_query)
