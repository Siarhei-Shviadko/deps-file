from typing import Protocol

from .group import Group

__all__ = ["ICommandGroupRepository"]


class ICommandGroupRepository(Protocol):
    def group_of_id(self, id_: str, tenant_id: str) -> Group | None:
        pass

    def save(self, group: Group) -> None:
        pass

    def delete(self, group: Group) -> None:
        pass

    def sync_groups(self, groups: list[Group]) -> None:
        pass
