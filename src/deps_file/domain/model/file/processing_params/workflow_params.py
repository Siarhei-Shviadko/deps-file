from typing import Literal, TypedDict

__all__ = ["WorkflowParamsDict"]


class WorkflowParamsDict(TypedDict):
    parsing_features: list[Literal["tables", "images", "kvps", "text"]]
    needs_unifier: bool
    needs_extraction: bool
    assigned_to_me: bool
    llm_type: str | None
    engine: str | None
    language: str | None
    metadata: dict | None
    document_type_id: str | None
