from dataclasses import dataclass

from deps_message_flow.events.common import DomainEvent

__all__ = ["GroupDeleted"]


@dataclass
class GroupDeleted(DomainEvent):
    id: str
    tenant_id: str
