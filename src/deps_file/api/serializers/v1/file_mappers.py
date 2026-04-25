from fastapi import Response

from deps_file.domain.model import FileDetailsInfo, FilesInfo

from .file_list import FileListMetaResponse, FileListResponse
from .file_reference_info import FileReferenceInfoResponse
from .file_response import (
    FileResponse,
    FileStateResponse,
    ProcessingParamsResponse,
    WorkflowParamsResponse,
)

__all__ = ["FileResponseMapper"]


class FileResponseMapper:
    @staticmethod
    def to_file_response(file_info: FileDetailsInfo) -> FileResponse:
        reference_data = file_info.get("reference")

        return FileResponse(
            id=file_info["file_id"],
            tenant_id=file_info["tenant_id"],
            name=file_info["name"],
            path=file_info["path"],
            state=FileStateResponse.model_validate(file_info["state"]),
            processing_params=ProcessingParamsResponse.model_validate(file_info.get("processing_params")),
            labels=file_info.get("labels") or [],
            reference=FileReferenceInfoResponse.model_validate(reference_data) if reference_data else None,
            created_at=file_info["created_at"],
            updated_at=file_info["updated_at"],
        )

    @staticmethod
    def to_file_list_response(files_info: FilesInfo) -> FileListResponse:
        return FileListResponse(
            meta=FileListMetaResponse(
                size=files_info["result_set"]["count"],
                total=files_info["result_set"]["total"],
            ),
            result=[FileResponseMapper.to_file_response(file_info) for file_info in files_info["files"]],
        )

    @staticmethod
    def to_file_content_response(content: bytes, file_name: str) -> Response:
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
            },
        )
