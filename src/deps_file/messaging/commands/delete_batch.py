from dataclasses import dataclass

from deps_message_flow.commands.common import Command

__all__ = ["DeleteBatchesWithDocuments"]


@dataclass
class DeleteBatchesWithDocuments(Command):
    batch_ids: list[str]
