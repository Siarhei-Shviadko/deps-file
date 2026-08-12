from dataclasses import dataclass
from typing import ClassVar, Literal

from deps_message_flow.commands.common import Command

__all__ = ["ProcessFileDomain"]


@dataclass
class ProcessFileDomain(Command):
    COMMAND_CHANNEL: ClassVar[str] = "FileCommands"
    REPLY_CHANNEL: ClassVar[str] = "FileCommandsReplies"

    file_id: str | None = None
    files: list[str] | None = None
    tenant_id: str | None = None
    parsing_features: list[Literal["tables", "images", "kvps", "text"]] | None = None
    engine: str | None = None
    language: str | None = None
