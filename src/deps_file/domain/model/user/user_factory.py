from .user import User
from .user_created import UserCreated

__all__ = ["UserFactory"]


class UserFactory:
    @staticmethod
    def make(id_: str, first_name: str, last_name: str) -> User:
        return User(
            id_=id_,
            first_name=first_name,
            last_name=last_name,
            events=[
                UserCreated(
                    id=id_,
                    first_name=first_name,
                    last_name=last_name,
                ),
            ],
        )
