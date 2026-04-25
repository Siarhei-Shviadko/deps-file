from typing import Any

from deps_file.domain.model import UserInfo

__all__ = ["UserInfoMapper"]


class UserInfoMapper:
    @staticmethod
    def from_row(user_row: dict[str, Any]) -> UserInfo:
        return UserInfo(
            id=user_row["user_id"],
            first_name=user_row["first_name"],
            last_name=user_row["last_name"],
        )
