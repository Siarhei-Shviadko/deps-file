from uuid import uuid4

import factory
from faker import Faker

from deps_file.domain.model import Group, GroupId
from deps_file.domain.model.shared import TenantId

__all__ = ["GroupFactory"]

fake = Faker()


class GroupFactory(factory.Factory):
    class Meta:
        model = Group

    id_ = factory.LazyFunction(lambda: GroupId().value)
    tenant_id = factory.LazyFunction(lambda: TenantId().value)
    is_deleted = False

    @classmethod
    def create_active(cls, **kwargs):
        defaults = {
            "is_deleted": False,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_for_tenant(cls, tenant_id: str, **kwargs):
        defaults = {
            "tenant_id": tenant_id,
            "is_deleted": False,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_deleted(cls, **kwargs):
        defaults = {
            "is_deleted": True,
        }
        defaults.update(kwargs)
        return cls(**defaults)
