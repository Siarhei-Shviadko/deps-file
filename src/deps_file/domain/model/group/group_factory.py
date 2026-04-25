from .group import Group

__all__ = ["GroupFactory"]


class GroupFactory:
    @classmethod
    def create(
        cls,
        id_: str,
        tenant_id: str,
        is_deleted: bool = False,
    ) -> Group:
        return Group(
            id_=id_,
            tenant_id=tenant_id,
            is_deleted=is_deleted,
        )
