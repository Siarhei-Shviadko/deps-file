from dataclasses import dataclass
from typing import Any

from deps_message_flow.commands.common import Command

from .command_with_error import CommandWithError

__all__ = ["ClassifyFile", "ClassifyFileReply"]


@dataclass
class ClassifyFile(Command):
    file_id: str
    file_name: str
    group_id: str
    file_path: str
    parsing_features: list[str] | None = None
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = None
    metadata: dict[str, Any] | None = None
    needs_unifier: bool = False
    needs_extraction: bool = True
    assigned_to_me: bool = False
    start_processing: bool = False


@dataclass
class ClassifyFileReply(CommandWithError):
    file_id: str
    document_id: str
    document_name: str
    document_type_id: str
    error_type: str | None = None
    error_message: str | None = None

    @property
    def has_error(self) -> bool:
        return self.error_type is not None
