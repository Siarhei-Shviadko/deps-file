from dataclasses import dataclass

from deps_message_flow.events.common import DomainEvent

__all__ = ["GroupCreated"]


@dataclass
class GroupCreated(DomainEvent):
    id: str
    tenant_id: str
