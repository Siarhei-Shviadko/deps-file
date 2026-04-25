from dataclasses import dataclass
from typing import Any, Literal

from deps_message_flow.commands.common import Command

__all__ = ["SplitFileDomain"]


@dataclass
class SplitFileDomain(Command):
    group_id: str
    classification_enabled: bool
    file_id: str | None = None
    file_name: str | None = None
    path: str | None = None
    document_type_id: str | None = None
    parsing_features: list[Literal["tables", "images", "kvps", "text"]] | None = None
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = None
    metadata: dict[str, Any] | None = None
    needs_unifier: bool = False
    needs_extraction: bool = True
    assigned_to_me: bool = False
