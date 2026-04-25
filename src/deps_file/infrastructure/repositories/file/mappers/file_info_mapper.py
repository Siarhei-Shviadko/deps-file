from typing import Any, Mapping

from sqlalchemy.engine import RowMapping

from deps_file.constants import DEFAULT_PAGE_SIZE
from deps_file.domain.model.file import FileDetailsInfo, FilesInfo
from deps_file.domain.model.shared import ResultSetInfo

__all__ = ["FileInfoMapper"]


class FileInfoMapper:
    @staticmethod
    def to_file_details_info(row: Mapping[str, Any]) -> FileDetailsInfo:
        raw_labels = row.get("labels")
        if raw_labels:
            labels = [label for label in raw_labels if label is not None] or None
        else:
            labels = None

        return FileDetailsInfo(
            file_id=row["file_id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            path=row["path"],
            state=row["state"],
            processing_params=row["processing_params"] or {},
            labels=labels,
            reference=row.get("reference"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def parse_rows_to_file_infos(
        records: list[RowMapping],
    ) -> list[FileDetailsInfo]:
        return [FileInfoMapper.to_file_details_info(row) for row in records]

    @staticmethod
    def parse_rows_to_files_info(records: list[RowMapping], total: int) -> FilesInfo:
        files = []
        for row in records:
            row_dict = dict(row)
            # Remove total_count column if present (from window function)
            row_dict.pop("total_count", None)
            files.append(FileInfoMapper.to_file_details_info(row_dict))

        count = len(files)
        offset = 0
        limit = count if count > 0 else DEFAULT_PAGE_SIZE

        result_set_info = ResultSetInfo(
            count=count,
            offset=offset,
            limit=limit,
            total=total,
        )

        return FilesInfo(files=files, result_set=result_set_info)
