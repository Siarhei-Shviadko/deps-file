from abc import ABC, abstractmethod
from typing import Any

__all__ = ["IDocumentProxy"]


class IDocumentProxy(ABC):
    @abstractmethod
    def create_document_from_file(
        self,
        file_name: str,
        file_content: bytes,
        document_type_id: str,
        group_id: str | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        parsing_features: list[str] | None = None,
        needs_unification: bool = True,
        needs_extraction: bool = True,
        needs_parsing: bool = False,
        assign_to_me: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        pass
