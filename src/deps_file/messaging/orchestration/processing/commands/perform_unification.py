from dataclasses import dataclass
from typing import Any

from deps_message_flow.commands.common import Command

from .command_with_error import CommandWithError

__all__ = ["PerformUnification", "PerformUnificationReply"]

CommonDict = dict[str, Any]


@dataclass
class PerformUnification(Command):
    # We're sending file_id instead of document_id. Here document_id is using for contract
    document_id: str
    files: list[str]
    document_type_id: str | None


@dataclass
class PerformUnificationReply(CommandWithError):
    error_type: str | None = None
    error_message: str | None = None

    @property
    def has_error(self) -> bool:
        return self.error_type is not None
