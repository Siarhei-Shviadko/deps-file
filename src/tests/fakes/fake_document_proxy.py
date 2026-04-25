from typing import Any

from deps_file.application.file import IDocumentProxy

__all__ = ["FakeDocumentProxy"]


class FakeDocumentProxy(IDocumentProxy):
    def __init__(self, document_id) -> None:
        self.document_id = document_id
        self.documents: list[dict[str, Any]] = []

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
        self.documents.append(
            {
                "file_name": file_name,
                "file_content": file_content,
                "document_type_id": document_type_id,
                "group_id": group_id,
                "engine": engine,
                "language": language,
                "llm_type": llm_type,
                "parsing_features": parsing_features,
                "needs_unification": needs_unification,
                "needs_extraction": needs_extraction,
                "needs_parsing": needs_parsing,
                "assign_to_me": assign_to_me,
                "metadata": metadata,
            }
        )
        return self.document_id, file_name
