from typing import TypedDict

__all__ = ["UserInfo"]


class UserInfo(TypedDict):
    id: str
    first_name: str
    last_name: str
