# flake8: noqa: C812,C813,C814,C815,C816,C818,C819
from ..shared import Guard, ImmutableCheck, TenantId
from .group_id import GroupId

__all__ = ["Group"]


class Group:
    id = Guard[GroupId](GroupId, ImmutableCheck())
    tenant_id = Guard[TenantId](TenantId, ImmutableCheck())
    is_deleted = Guard[bool](bool)

    def __init__(
        self,
        id_: str | None,
        tenant_id: str,
        *,
        is_deleted: bool = False,
    ) -> None:
        self.id = GroupId(id_) if id_ is not None else GroupId()
        self.tenant_id = TenantId(tenant_id)
        self.is_deleted = is_deleted

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __repr__(self) -> str:
        return " ".join(
            (
                f"{self.__class__.__name__}(id_={self.id},",
                f"tenant_id={self.tenant_id},",
                f"is_deleted={self.is_deleted})",
            ),
        )

    def delete(self) -> None:
        self.is_deleted = True
