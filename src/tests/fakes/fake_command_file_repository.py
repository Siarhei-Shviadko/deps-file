import logging
from copy import deepcopy
from typing import Optional

from deps_file.domain.model.file import File, ICommandFileRepository

__all__ = ["FakeCommandFileRepository"]


class FakeCommandFileRepository(ICommandFileRepository):
    def __init__(self, files: Optional[list[File]] = None) -> None:
        self._db: dict[tuple[str, str], File] = {}
        if files:
            for file in files:
                key = (file.id(), file.tenant_id())
                self._db[key] = file

        self._logger = logging.getLogger(self.__class__.__name__)

    def file_of_id(self, id_: str, tenant_id: str) -> Optional[File]:
        return self._db.get((id_, tenant_id))

    def files_of_ids(self, ids: set[str], tenant_id: str) -> list[File]:
        files = []
        for file_id in ids:
            file = self._db.get((file_id, tenant_id))
            if file:
                files.append(file)
        return files

    def save(self, file: File) -> None:
        file = deepcopy(file)
        file.events.clear()
        file.commands.clear()
        key = (file.id(), file.tenant_id())
        self._db[key] = file
        self._logger.debug(f"Saved file {file.id} for tenant {file.tenant_id}")

    def delete_all(self, files: list[File]) -> None:
        for file in files:
            key = (file.id(), file.tenant_id())
            if key in self._db:
                del self._db[key]
                self._logger.debug(f"Deleted file {file.id} for tenant {file.tenant_id}")
