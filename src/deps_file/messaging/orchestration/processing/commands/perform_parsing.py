from dataclasses import dataclass

from deps_message_flow.commands.common import Command

from .command_with_error import CommandWithError

__all__ = ["PerformParsing", "PerformParsingReply"]


@dataclass
class PerformParsing(Command):
    tenant_id: str
    document_id: str
    files: list[str]
    engine: str | None
    features: list[str] | None = None
    document_type_id: str | None = None
    language: str | None = None


@dataclass
class PerformParsingReply(CommandWithError):
    error_type: str | None = None
    error_message: str | None = None

    @property
    def has_error(self) -> bool:
        return self.error_type is not None
