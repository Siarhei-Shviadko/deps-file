import logging
from typing import Optional

from deps_file.domain.model import Group, ICommandGroupRepository

__all__ = ["FakeCommandGroupRepository"]


class FakeCommandGroupRepository(ICommandGroupRepository):
    def __init__(self, groups: Optional[list[Group]] = None) -> None:
        self._db: dict[tuple[str, str], Group] = {}
        self._save_calls: list[Group] = []
        self._delete_calls: list[Group] = []

        if groups:
            for group in groups:
                key = (str(group.id()), str(group.tenant_id()))
                self._db[key] = group

        self._logger = logging.getLogger(self.__class__.__name__)

    def group_of_id(self, group_id: str, tenant_id: str) -> Optional[Group]:
        group = self._db.get((group_id, tenant_id))
        if group and not group.is_deleted:
            return group
        return None

    def save(self, group: Group) -> None:
        key = (str(group.id()), str(group.tenant_id()))
        self._db[key] = group
        self._save_calls.append(group)
        self._logger.debug(f"Saved group {group.id()} for tenant {group.tenant_id()}")

    def delete(self, group: Group) -> None:
        group.delete()
        self.save(group)
        self._delete_calls.append(group)
        self._logger.debug(f"Deleted group {group.id()} for tenant {group.tenant_id()}")

    def get_saved_groups(self) -> list[Group]:
        return self._save_calls.copy()

    def get_deleted_groups(self) -> list[Group]:
        return self._delete_calls.copy()

    def clear_calls(self) -> None:
        self._save_calls.clear()
        self._delete_calls.clear()

    def get_all_groups_including_deleted(self, tenant_id: str) -> list[Group]:
        return [group for (gid, tid), group in self._db.items() if tid == tenant_id]
