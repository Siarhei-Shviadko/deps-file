from typing import Self

from pydantic import Field, model_validator

from deps_file.application import BatchFileDict

from ..base import BaseSerializer

__all__ = ["BatchCreationRequest"]


class SerializedBatchFile(BaseSerializer):
    name: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    document_type_id: str | None = Field(None, alias="documentTypeId")


class BatchCreationRequest(BaseSerializer):
    batch_name: str = Field(..., alias="batchName")
    files: list[SerializedBatchFile] = Field(..., min_length=1)
    group_id: str | None = Field(None, alias="groupId")

    @property
    def batch_files(self) -> list[BatchFileDict]:
        return [BatchFileDict(name=bf.name, path=bf.path, document_type_id=bf.document_type_id) for bf in self.files]

    @model_validator(mode="after")
    def validate_group_or_document_types_existence(self) -> Self:
        if self.group_id is None and any(f.document_type_id is None for f in self.files):
            raise ValueError("Group id or all file document type ids should be provided")

        return self
