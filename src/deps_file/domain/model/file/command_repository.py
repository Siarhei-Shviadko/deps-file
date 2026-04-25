from typing import Optional, Protocol

from .file import File

__all__ = ["ICommandFileRepository"]


class ICommandFileRepository(Protocol):
    def file_of_id(self, id_: str, tenant_id: str) -> Optional[File]:
        pass

    def files_of_ids(self, ids: set[str], tenant_id: str) -> list[File]:
        pass

    def save(self, file: File) -> None:
        pass

    def delete_all(self, files: list[File]) -> None:
        pass
