from abc import ABC, abstractmethod

__all__ = ["IGroupProxy"]


class IGroupProxy(ABC):
    @abstractmethod
    def get_all_groups(self) -> list:  # noqa: WPS463
        pass
