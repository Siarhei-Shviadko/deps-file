from datetime import datetime

from pydantic import BaseModel, Field

from deps_file.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIRECTION,
    DEFAULT_SORT_FIELD,
    MAX_PAGE_SIZE,
)

__all__ = ["FileListQueryParams"]


class FileListQueryParams(BaseModel):
    page: int = Field(DEFAULT_PAGE_NUMBER, ge=DEFAULT_PAGE_NUMBER, description="Page number")
    size: int = Field(
        DEFAULT_PAGE_SIZE,
        ge=DEFAULT_PAGE_NUMBER,
        le=MAX_PAGE_SIZE,
        description="Page size",
    )

    name: str | None = Field(None, description="Filter by name (partial match)")
    state: str | None = Field(None, description="Filter by state")
    labels: list[str] | None = Field(None, description="Filter by labels (match any)")
    date_start: datetime | None = Field(None, description="Filter by creation date start (inclusive)")
    date_end: datetime | None = Field(None, description="Filter by creation date end (inclusive)")
    reference_available: bool | None = Field(
        None,
        alias="referenceAvailable",
        description="Filter by reference availability",
    )
    entity_name: str | None = Field(None, alias="reference", description="Filter by reference name (partial match)")

    sort_by: str = Field(DEFAULT_SORT_FIELD, description="Sort field")
    sort_direction: str = Field(DEFAULT_SORT_DIRECTION, description="Sort direction")
