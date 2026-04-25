from typing import Any

from sqlalchemy import Column, and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import Insert, Select

from deps_file.domain.model import Group

from ..tables import group_table
from .mappers import GroupInfoMapper, GroupMapper

__all__ = ["QueryGroupFactory"]


class QueryGroupFactory:
    @staticmethod
    def create_group_info(data: dict[str, Any]) -> dict[str, Any]:
        return GroupInfoMapper.from_dict(data)

    @property
    def group_columns(self) -> list[Column]:
        return [
            group_table.c.group_id,
            group_table.c.tenant_id,
            group_table.c.is_deleted,
        ]

    @staticmethod
    def find_group(id_: str, tenant_id: str) -> Select:
        return select(group_table.columns).where(
            and_(
                group_table.c.group_id == id_,
                group_table.c.tenant_id == tenant_id,
                group_table.c.is_deleted.is_(False),
            ),
        )

    @staticmethod
    def find_groups(tenant_id: str) -> Select:
        return select(group_table.columns).where(
            and_(
                group_table.c.tenant_id == tenant_id,
                group_table.c.is_deleted.is_(False),
            ),
        )

    @staticmethod
    def save_group(group: Group) -> Insert:
        group_dict = GroupMapper.to_dict(group)

        return (
            insert(group_table).values(**group_dict).on_conflict_do_update(index_elements=["group_id"], set_=group_dict)
        )

    @staticmethod
    def save_group_fields(groups: list[Group]) -> Insert:
        data = [GroupMapper.to_dict(group) for group in groups]

        return (
            insert(group_table)
            .on_conflict_do_update(
                index_elements=[group_table.c.group_id],
                set_={
                    "is_deleted": insert(group_table).excluded.is_deleted,
                },
            )
            .values(data)
        )
