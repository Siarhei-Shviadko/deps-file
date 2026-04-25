from typing import List, Protocol

from .group import Group

__all__ = ["IGroupRepository"]


class IGroupRepository(Protocol):
    def group_of_id(self, id_: str, tenant_id: str) -> Group | None:
        pass

    def has_group(self, id_: str, tenant_id: str) -> bool:
        pass

    def find_all(self, tenant_id: str) -> List[Group]:
        pass
