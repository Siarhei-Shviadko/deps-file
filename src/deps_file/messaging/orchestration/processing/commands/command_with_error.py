from abc import ABC, abstractmethod

__all__ = ["CommandWithError"]


class CommandWithError(ABC):
    @property
    @abstractmethod
    def has_error(self) -> bool:
        ...  # noqa: WPS428
