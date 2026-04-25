from typing import TypedDict

__all__ = ["GroupInfo"]


class GroupInfo(TypedDict):
    id: str
    tenant_id: str
    is_deleted: bool
