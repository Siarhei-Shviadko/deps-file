from dataclasses import dataclass
from typing import Any

from deps_message_flow.commands.common import Command

__all__ = ["SplitFile", "SplitFileReply"]


@dataclass
class SplitFile(Command):
    file_id: str
    file_name: str
    group_id: str
    file_path: str
    document_type_id: str
    classification_enabled: bool
    parsing_features: list[str] | None = None
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = None
    metadata: dict[str, Any] | None = None
    needs_unifier: bool = False
    needs_extraction: bool = True
    assigned_to_me: bool = False


@dataclass
class SplitFileReply(Command):
    file_id: str
    batch_id: str | None = None
    batch_name: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    @property
    def has_error(self) -> bool:
        return self.error_type is not None
