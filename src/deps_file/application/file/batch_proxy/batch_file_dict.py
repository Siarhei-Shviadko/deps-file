from typing import TypedDict

__all__ = ["BatchFileDict"]


class BatchFileDict(TypedDict):
    name: str
    path: str
    document_type_id: str | None
