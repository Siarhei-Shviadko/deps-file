from uuid import uuid4

import pytest

from deps_file.domain.exceptions import IllegalArgument
from deps_file.domain.model import Group, GroupId
from deps_file.domain.model.shared import TenantId
from tests.factories import GroupFactory
from tests.shared_fixtures.group import (
    test_group_1,
    test_group_1_id,
    test_group_1_tenant_id,
    test_group_2,
    test_group_2_id,
    test_group_2_tenant_id,
    test_group_for_deletion,
    test_group_minimal,
    test_groups_different_tenants,
)


def test_create__with_complete_data__created(
    tenant_id,
    test_group_1,
    test_group_1_id,
    test_group_1_tenant_id,
):
    assert test_group_1.id() == test_group_1_id.value
    assert test_group_1.tenant_id() == tenant_id()
    assert test_group_1.is_deleted is False


def test_create__with_minimal_data__created(test_group_minimal):
    assert test_group_minimal.id() is not None
    assert test_group_minimal.tenant_id() is not None
    assert test_group_minimal.is_deleted is False


def test_create__with_none_id__generates_id():
    tenant_id = str(uuid4())
    group = Group(
        id_=None,
        tenant_id=tenant_id,
    )
    assert group.id() is not None
    assert isinstance(group.id, GroupId)


def test_create__with_provided_id__uses_provided_id():
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    group = Group(
        id_=group_id,
        tenant_id=tenant_id,
    )

    assert group.id() == group_id


def test_delete__active_group__sets_deleted_flag(test_group_for_deletion):
    assert test_group_for_deletion.is_deleted is False

    test_group_for_deletion.delete()

    assert test_group_for_deletion.is_deleted is True


def test_delete__already_deleted__remains_deleted():
    group = GroupFactory.create_deleted()
    assert group.is_deleted is True

    group.delete()

    assert group.is_deleted is True


def test_equality__different_id__not_equal(test_group_1, test_group_2):
    assert test_group_1 != test_group_2


def test_repr__group_object__contains_all_fields(test_group_1):
    repr_str = repr(test_group_1)

    assert "Group(" in repr_str
    assert test_group_1.id() in repr_str
    assert test_group_1.tenant_id() in repr_str
    assert str(test_group_1.is_deleted) in repr_str


def test_immutable_fields__id_cannot_change(test_group_1):
    original_id = test_group_1.id()

    with pytest.raises(IllegalArgument):
        test_group_1.id = GroupId()

    assert test_group_1.id() == original_id


def test_immutable_fields__tenant_id_cannot_change(test_group_1):
    original_tenant_id = test_group_1.tenant_id()

    with pytest.raises(IllegalArgument):
        test_group_1.tenant_id = TenantId()

    assert test_group_1.tenant_id() == original_tenant_id


def test_mutable_fields__deleted_flag_can_change(test_group_1):
    assert test_group_1.is_deleted is False

    test_group_1.is_deleted = True

    assert test_group_1.is_deleted is True


def test_tenant_isolation__different_tenants__different_groups(test_groups_different_tenants):
    group_1, group_2 = test_groups_different_tenants

    assert group_1.tenant_id() != group_2.tenant_id()
    assert group_1.id() != group_2.id()
    assert group_1 != group_2
