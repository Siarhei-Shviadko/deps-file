from typing import Any, Optional

from sqlalchemy.orm import Session

from deps_file.domain.model.file import File, ICommandFileRepository

from .mappers import FileMapper
from .query_factory import QueryFileFactory

__all__ = ["UoWCommandFileRepository"]


class UoWCommandFileRepository(ICommandFileRepository):
    def __init__(self, connection: Session) -> None:
        self._connection = connection
        self._query_factory = QueryFileFactory()

    def file_of_id(self, id_: str, tenant_id: str) -> Optional[File]:
        query = self._query_factory.find_file(id_, tenant_id)
        row = self._connection.execute(query).mappings().first()

        if not row:
            return None

        return FileMapper.from_dict(dict(row))

    def files_of_ids(self, ids: set[str], tenant_id: str) -> list[File]:
        if not ids:
            return []

        query = self._query_factory.find_files_by_ids(ids, tenant_id)
        rows = self._connection.execute(query).mappings().all()

        return [FileMapper.from_dict(dict(row)) for row in rows]

    def save(self, file: File) -> None:
        file_dict = FileMapper.to_dict(file)
        labels = file_dict.pop("labels", None)
        reference = file_dict.pop("reference", None)

        self._save_file(file_dict)

        if labels is not None:
            self._save_labels(labels, file_id=file.id())

        if reference is not None:
            reference["file_id"] = file.id()
            self._save_reference(reference)

    def delete_all(self, file: list[File]) -> None:
        file_ids = [f.id() for f in file]
        tenant_id = file[0].tenant_id()
        delete_queries = self._query_factory.delete_files(file_ids, tenant_id)
        for query in delete_queries:
            self._connection.execute(query)

    def _save_file(self, file_dict: dict[str, Any]) -> None:
        save_file_query = self._query_factory.save_file(file_dict)
        self._connection.execute(save_file_query, file_dict)

    def _save_labels(self, labels: list[str], *, file_id: str) -> None:
        save_labels_query = self._query_factory.save_labels()
        labels_list = [{"content": label} for label in labels]
        saved_labels = self._connection.execute(save_labels_query, labels_list).scalars().all()
        self._save_labels_to_file(saved_labels, file_id=file_id)

    def _save_labels_to_file(self, saved_labels: list[tuple[int]], *, file_id: str) -> None:
        values = [{"file_id": file_id, "label_id": label_id} for label_id in saved_labels]
        save_labels_to_file_query = self._query_factory.save_labels_to_file()
        self._connection.execute(save_labels_to_file_query, values)

    def _save_reference(self, reference: dict[str, Any]) -> None:
        save_reference_query = self._query_factory.save_reference()
        self._connection.execute(save_reference_query, reference)
