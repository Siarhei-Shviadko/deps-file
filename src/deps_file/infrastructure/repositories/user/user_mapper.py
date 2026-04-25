from typing import Any

from deps_file.domain.model import User

__all__ = ["UserMapper"]


class UserMapper:
    @staticmethod
    def to_dict(user: User) -> dict[str, Any]:
        return {
            "user_id": user.id(),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    @staticmethod
    def from_dict(user: dict[str, Any]) -> User:
        return User(
            id_=user["user_id"],
            first_name=user["first_name"],
            last_name=user["last_name"],
        )
