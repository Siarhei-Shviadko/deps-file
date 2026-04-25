from .base import NotFoundError

__all__ = ["UserNotFound"]


class UserNotFound(NotFoundError):
    code = "user_not_found"

    def __init__(self, user_id: str) -> None:
        super().__init__(f"User with id `{user_id}` not found.")
