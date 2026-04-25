from typing import Any

from deps_file.domain.model.file import File

from .processing_params_mapper import ProcessingParamsMapper
from .reference_mapper import ReferenceMapper
from .state_mapper import StateMapper

__all__ = ["FileMapper"]


class FileMapper:
    @staticmethod
    def to_dict(file: File) -> dict[str, Any]:
        return {
            "file_id": file.id(),
            "tenant_id": file.tenant_id(),
            "name": file.name,
            "path": file.path,
            "state": StateMapper.to_dict(file.state),
            "processing_params": ProcessingParamsMapper.to_dict(file.processing_params),
            "created_at": file.created_at,
            "updated_at": file.updated_at,
            "labels": file.labels if file.labels else None,
            "reference": ReferenceMapper.to_dict(file.reference) if file.reference else None,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> File:
        processing_params = ProcessingParamsMapper.from_dict(data.get("processing_params"))
        state = StateMapper.from_dict(data.get("state"))

        return File(
            id_=data["file_id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            path=data["path"],
            state=state,
            processing_params=processing_params,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            labels=data.get("labels", None),
            reference=ReferenceMapper.from_dict(data.get("reference")) if data.get("reference") else None,
        )
