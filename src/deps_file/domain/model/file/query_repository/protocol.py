from typing import Optional, Protocol

from ...shared import Pagination
from ..file_info import FileDetailsInfo, FilesInfo
from .filtering import FileFiltering
from .sorting import FileSorting

__all__ = ["IQueryFileRepository"]


class IQueryFileRepository(Protocol):
    def find_all_with(
        self,
        filtering: FileFiltering,
        sorting: FileSorting,
        pagination: Pagination,
    ) -> FilesInfo:
        pass

    def find_file(self, file_id: str, tenant_id: str) -> Optional[FileDetailsInfo]:
        pass
