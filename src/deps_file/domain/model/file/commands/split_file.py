from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from deps_message_flow.commands.common import Command

from deps_file.constants import SPLIT_COMMANDS_CHANNEL

__all__ = ["SplitFile"]


@dataclass
class SplitFile(Command):
    COMMAND_CHANNEL: ClassVar[str] = SPLIT_COMMANDS_CHANNEL
    REPLY_CHANNEL: ClassVar[str] = "SplittingCommandsReply"

    group_id: str
    document_type_id: str | None
    classification_enabled: bool
    file_id: str | None = None
    file_name: str | None = None
    path: str | None = None
    needs_splitting_proposal_review: bool = True
    parsing_features: list[Literal["tables", "images", "kvps", "text"]] | None = None
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = None
    metadata: dict[str, Any] | None = None
    needs_unifier: bool = False
    needs_extraction: bool = True
    assigned_to_me: bool = False
