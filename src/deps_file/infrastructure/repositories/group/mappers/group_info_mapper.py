from typing import Any

__all__ = ["GroupInfoMapper"]


class GroupInfoMapper:
    @staticmethod
    def from_dict(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data["group_id"],
            "tenant_id": data["tenant_id"],
            "is_deleted": data["is_deleted"],
        }
