from typing import List

from pydantic import BaseModel

from .file_response import FileResponse

__all__ = ["FileListMetaResponse", "FileListResponse"]


class FileListMetaResponse(BaseModel):
    size: int
    total: int


class FileListResponse(BaseModel):
    meta: FileListMetaResponse
    result: List[FileResponse]
