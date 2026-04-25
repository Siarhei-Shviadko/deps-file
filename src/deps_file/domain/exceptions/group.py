from .base import NotFoundError

__all__ = ["GroupNotFound"]


class GroupNotFound(NotFoundError):
    code = "group_not_found"

    def __init__(self, group_id: str) -> None:
        super().__init__(f"Group with id `{group_id}` not found.")
