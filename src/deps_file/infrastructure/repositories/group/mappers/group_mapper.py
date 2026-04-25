from typing import Any

from deps_file.domain.model import Group

__all__ = ["GroupMapper"]

Row = dict[str, Any]


class GroupMapper:
    @staticmethod
    def to_dict(group: Group) -> dict[str, Any]:
        return {
            "group_id": group.id(),
            "tenant_id": group.tenant_id(),
            "is_deleted": group.is_deleted,
        }

    @staticmethod
    def from_dict(data: Row) -> Group:
        return Group(
            id_=data.get("group_id") or data.get("id"),
            tenant_id=data["tenant_id"],
            is_deleted=data["is_deleted"],
        )
