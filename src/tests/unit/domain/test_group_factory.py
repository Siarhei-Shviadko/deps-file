from uuid import uuid4

import pytest

from deps_file.domain.model import Group
from tests.factories import GroupFactory


def test_create__with_minimal_data__created():
    group = GroupFactory()

    assert isinstance(group, Group)
    assert group.id() is not None
    assert group.tenant_id() is not None
    assert group.is_deleted is False


def test_create__with_complete_data__created():
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    group = GroupFactory(
        id_=group_id,
        tenant_id=tenant_id,
    )

    assert group.id() == group_id
    assert group.tenant_id() == tenant_id
    assert group.is_deleted is False


def test_create__generates_unique_ids__all_unique():
    group_1 = GroupFactory()
    group_2 = GroupFactory()
    group_3 = GroupFactory()

    assert group_1.id() != group_2.id()
    assert group_2.id() != group_3.id()
    assert group_1.id() != group_3.id()


def test_create__with_custom_params__uses_custom_values():
    custom_tenant = str(uuid4())

    group = GroupFactory(tenant_id=custom_tenant)

    assert group.tenant_id() == custom_tenant


def test_create_active__default_state__not_deleted():
    group = GroupFactory.create_active()

    assert group.is_deleted is False
    assert isinstance(group, Group)


def test_create_active__with_custom_tenant__uses_custom_tenant():
    custom_tenant = str(uuid4())

    group = GroupFactory.create_active(tenant_id=custom_tenant)

    assert group.tenant_id() == custom_tenant
    assert group.is_deleted is False


def test_create_for_tenant__with_tenant_id__proper_tenant():
    tenant_id = str(uuid4())

    group = GroupFactory.create_for_tenant(tenant_id=tenant_id)

    assert group.tenant_id() == tenant_id
    assert group.is_deleted is False


def test_create_for_tenant__with_additional_params__uses_all_params():
    tenant_id = str(uuid4())

    group = GroupFactory.create_for_tenant(
        tenant_id=tenant_id,
        is_deleted=True,
    )

    assert group.tenant_id() == tenant_id
    assert group.is_deleted is True


def test_create_deleted__creates_deleted_group():
    group = GroupFactory.create_deleted()

    assert group.is_deleted is True
    assert isinstance(group, Group)


def test_create_deleted__with_custom_params__uses_custom_values():
    custom_tenant = str(uuid4())

    group = GroupFactory.create_deleted(tenant_id=custom_tenant)

    assert group.tenant_id() == custom_tenant
    assert group.is_deleted is True


def test_factory_sequence__unique_ids():
    group_1 = GroupFactory()
    group_2 = GroupFactory()

    assert group_1.id() != group_2.id()
    assert group_1.tenant_id() != group_2.tenant_id()


def test_factory_methods__different_configurations__all_valid():
    active_group = GroupFactory.create_active()
    tenant_group = GroupFactory.create_for_tenant(tenant_id=str(uuid4()))
    deleted_group = GroupFactory.create_deleted()

    assert active_group.is_deleted is False
    assert tenant_group.is_deleted is False
    assert deleted_group.is_deleted is True

    assert len({group.id() for group in [active_group, tenant_group, deleted_group]}) == 3
