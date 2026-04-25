from typing import Optional

from deps_file.domain.model.file import File, FileDetailsInfo, IQueryFileRepository
from deps_file.infrastructure.repositories.file.mappers import ReferenceMapper

__all__ = ["FakeQueryFileRepository"]


class FakeQueryFileRepository(IQueryFileRepository):
    def __init__(self, files: Optional[list[File]] = None) -> None:
        self._db: dict[tuple[str, str], File] = {}
        if files:
            for file in files:
                key = (file.id(), file.tenant_id())
                self._db[key] = file

    def find_file(self, file_id: str, tenant_id: str) -> Optional[FileDetailsInfo]:
        file = self._db.get((file_id, tenant_id))
        if not file:
            return None
        return FileDetailsInfo(
            file_id=file.id(),
            tenant_id=file.tenant_id(),
            name=file.name,
            path=file.path,
            state={"status": file.state.status.value},
            processing_params={
                "group_id": str(file.processing_params.group_id()) if file.processing_params.group_id else None,
                "splitting_enabled": file.processing_params.splitting_enabled,
                "classification_enabled": file.processing_params.classification_enabled,
                "workflow_params": file.processing_params.workflow_params,
            },
            labels=None,
            reference=ReferenceMapper.to_dict(file.reference) if file.reference else None,
            created_at=file.created_at,
            updated_at=file.updated_at,
        )

    def file_of_id(self, id_: str, tenant_id: str) -> Optional[FileDetailsInfo]:
        return self.find_file(file_id=id_, tenant_id=tenant_id)
