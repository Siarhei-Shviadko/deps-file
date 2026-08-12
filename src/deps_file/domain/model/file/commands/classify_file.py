from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from deps_message_flow.commands.common import Command

__all__ = ["ClassifyFileDomain"]


@dataclass
class ClassifyFileDomain(Command):
    COMMAND_CHANNEL: ClassVar[str] = "FileCommands"
    REPLY_CHANNEL: ClassVar[str] = "FileCommandsReplies"

    group_id: str
    file_id: str | None = None
    file_name: str | None = None
    path: str | None = None
    engine: str | None = None
    language: str | None = None
    parsing_features: list[Literal["tables", "images", "kvps", "text"]] | None = None
    llm_type: str | None = None
    needs_unifier: bool = False
    needs_extraction: bool = False
    assigned_to_me: bool = False
    metadata: dict[str, Any] | None = None
