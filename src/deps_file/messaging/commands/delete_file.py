from dataclasses import dataclass

from deps_message_flow.commands.common import Command

__all__ = ["DeleteFile"]


@dataclass
class DeleteFile(Command):
    file_ids: list[str]
