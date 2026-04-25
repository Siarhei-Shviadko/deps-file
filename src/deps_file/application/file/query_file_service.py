from datetime import datetime

from deps_file.domain.exceptions import FileNotFound
from deps_file.domain.model import (
    FileDetailsInfo,
    FileFiltering,
    FilesInfo,
    FileSortBy,
    FileSorting,
    FileSortOrder,
    IQueryFileRepository,
    Pagination,
)

__all__ = ["QueryFileService"]


class QueryFileService:
    def __init__(self, query_file_repository: IQueryFileRepository) -> None:
        self._query_file_repository = query_file_repository

    def find_file(self, file_id: str, tenant_id: str) -> FileDetailsInfo:
        if file := self._query_file_repository.find_file(file_id=file_id, tenant_id=tenant_id):
            return file

        raise FileNotFound(file_id)

    def find_all_with(
        self,
        tenant_id: str,
        name: str | None,
        state: list[str] | None,
        labels: list[str] | None,
        date_start: datetime | None,
        date_end: datetime | None,
        reference_available: bool | None,
        entity_name: str | None,
        page: int,
        per_page: int,
        sort_by: FileSortBy,
        sort_order: FileSortOrder,
    ) -> FilesInfo:
        return self._query_file_repository.find_all_with(
            filtering=FileFiltering(
                tenant_id=tenant_id,
                name=name,
                state=state,
                labels=labels,
                date_start=date_start,
                date_end=date_end,
                reference_available=reference_available,
                entity_name=entity_name,
            ),
            sorting=FileSorting(sort_by=sort_by, sort_order=sort_order),
            pagination=Pagination(page=page, per_page=per_page),
        )
