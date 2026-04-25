from dataclasses import dataclass

from ...shared import ExtendedEnum

__all__ = ["FileSortBy", "FileSorting", "FileSortOrder"]


class FileSortOrder(ExtendedEnum):
    ASC = "asc"
    DESC = "desc"


class FileSortBy(ExtendedEnum):
    NAME = "name"
    STATE = "state"
    CREATED_AT = "createdAt"


@dataclass
class FileSorting:
    sort_by: FileSortBy = FileSortBy.CREATED_AT
    sort_order: FileSortOrder = FileSortOrder.DESC
