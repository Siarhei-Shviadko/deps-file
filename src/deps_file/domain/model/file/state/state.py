from ...shared import Guard, ImmutableCheck
from .error_code import ErrorCode
from .status import Status

__all__ = ["State"]


class State:
    status = Guard[Status](Status, ImmutableCheck())
    error_message = Guard[str](str, ImmutableCheck())
    error_code = Guard[str](str, ImmutableCheck())

    def __init__(
        self,
        status: str | Status,
        error_message: str | None = None,
        error_code: ErrorCode | None = None,
    ) -> None:
        try:
            self.status = status if isinstance(status, Status) else Status(status)
        except ValueError:
            raise ValueError(f"Invalid status: {status}")

        if error_message:
            self.error_message = error_message

        if error_code:
            self.error_code = error_code

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return (
            self.status == other.status
            and self.error_message == other.error_message
            and self.error_code == other.error_code
        )

    def __repr__(self) -> str:
        return (
            f"<class '{self.__class__.__name__}': "
            f"{self.status=}, "
            f"{self.error_message=}, "
            f"{self.error_code=}>"
        )
