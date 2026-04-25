from .error_type import ErrorType

__all__ = ["Error"]


class Error:
    def __init__(self, type_: ErrorType, message: str) -> None:
        self._type = type_
        self._message = message

    def __str__(self) -> str:
        return f"<Error>: {self._type}, {self._message}"

    @property
    def type(self) -> ErrorType:
        return self._type

    @property
    def message(self) -> str:
        return self._message

    @property
    def is_business(self) -> bool:
        return self._type == ErrorType.BUSINESS

    @property
    def is_system(self) -> bool:
        return self._type == ErrorType.SYSTEM
