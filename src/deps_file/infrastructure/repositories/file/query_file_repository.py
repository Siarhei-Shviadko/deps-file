from typing import Optional

from deps_file.domain.model.file import (
    FileDetailsInfo,
    FileFiltering,
    FilesInfo,
    FileSorting,
    IQueryFileRepository,
)
from deps_file.domain.model.shared import Pagination
from deps_file.extras.database_session import DatabaseSession

from .mappers import FileInfoMapper
from .query_factory import QueryFileFactory

__all__ = ["QueryFileRepository"]


class QueryFileRepository(IQueryFileRepository):
    def __init__(self, database: DatabaseSession) -> None:
        self._db = database
        self._query_factory = QueryFileFactory()

    def find_all_with(
        self,
        filtering: FileFiltering,
        sorting: FileSorting,
        pagination: Pagination,
    ) -> FilesInfo:
        valid_files_query = self._query_factory.filtered_file_ids(
            filtering=filtering,
            sorting=sorting,
            pagination=pagination,
        )
        query = self._query_factory.find_all_with_count(valid_files_query, sorting=sorting)

        with self._db.connection() as conn:
            records = conn.execute(query).mappings().all()
            total = records[0]["total_count"] if records else 0
            return FileInfoMapper.parse_rows_to_files_info(records, total)

    def find_file(self, file_id: str, tenant_id: str) -> Optional[FileDetailsInfo]:
        query = self._query_factory.find_file(file_id=file_id, tenant_id=tenant_id)
        with self._db.connection() as conn:
            row = conn.execute(query).mappings().first()
            if not row:
                return None
            return FileInfoMapper.to_file_details_info(row)

    def file_of_id(self, file_id: str, tenant_id: str) -> Optional[FileDetailsInfo]:
        return self.find_file(file_id, tenant_id)
