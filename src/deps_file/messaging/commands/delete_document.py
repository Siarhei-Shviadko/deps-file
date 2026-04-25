from dataclasses import dataclass

from deps_message_flow.commands.common import Command

__all__ = ["DeleteDocument"]


@dataclass
class DeleteDocument(Command):
    document_id: str
