from datetime import datetime
from typing import Any, TypedDict

from ..shared import ResultSetInfo

__all__ = ["FileDetailsInfo", "FilesInfo"]


class FileDetailsInfo(TypedDict):
    file_id: str
    tenant_id: str
    name: str
    path: str
    state: dict[str, Any]
    processing_params: dict[str, Any]
    labels: list[str] | None
    reference: dict[str, str] | None
    created_at: datetime
    updated_at: datetime | None


class FilesInfo(TypedDict):
    files: list[FileDetailsInfo]
    result_set: ResultSetInfo
