from uuid import uuid4

import pytest

from tests.factories import GroupFactory
from tests.shared_fixtures.group import (
    test_group_1,
    test_group_1_id,
    test_group_1_tenant_id,
    test_group_2,
    test_group_2_id,
    test_group_2_tenant_id,
    test_group_minimal,
)


def test_find_group(test_group_1, unit_of_work, add_single_group):
    add_single_group(test_group_1)

    with unit_of_work:
        found_group = unit_of_work.groups.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())

    assert found_group is not None
    assert found_group.id() == test_group_1.id()
    assert found_group.tenant_id() == test_group_1.tenant_id()
    assert found_group.is_deleted == test_group_1.is_deleted


def test_find_group__not_found(unit_of_work, test_group_1_tenant_id):
    with unit_of_work:
        result = unit_of_work.groups.group_of_id(id_=str(uuid4()), tenant_id=test_group_1_tenant_id())

    assert result is None


def test_find_group__wrong_tenant(test_group_1, test_group_2_tenant_id, unit_of_work, add_single_group):
    add_single_group(test_group_1)

    with unit_of_work:
        result = unit_of_work.groups.group_of_id(id_=test_group_1.id(), tenant_id=test_group_2_tenant_id())

    assert result is None


def test_find_group__deleted_group__returns_none(test_group_1, unit_of_work, add_single_group):
    test_group_1.delete()
    add_single_group(test_group_1)

    with unit_of_work:
        result = unit_of_work.groups.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())

    assert result is None


def test_save__new_group(test_group_1, unit_of_work, command_group_repository):
    with unit_of_work:
        unit_of_work.groups.save(test_group_1)
        unit_of_work.commit()

    found_group = command_group_repository.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())

    assert found_group is not None
    assert found_group.id() == test_group_1.id()


def test_save__multiple_groups(test_group_1, test_group_2, unit_of_work, command_group_repository):
    with unit_of_work:
        unit_of_work.groups.save(test_group_1)
        unit_of_work.groups.save(test_group_2)
        unit_of_work.commit()

    group_1 = command_group_repository.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())
    group_2 = command_group_repository.group_of_id(id_=test_group_2.id(), tenant_id=test_group_2.tenant_id())

    assert group_1 is not None
    assert group_2 is not None
    assert group_1.id() == test_group_1.id()
    assert group_2.id() == test_group_2.id()


def test_save__soft_deleted_group__persisted_with_deleted_flag(test_group_1, unit_of_work, command_group_repository):
    test_group_1.delete()

    with unit_of_work:
        unit_of_work.groups.save(test_group_1)
        unit_of_work.commit()

    found_group = command_group_repository.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())

    assert found_group is None


def test_save__with_complete_data(integration_group_with_complete_data, unit_of_work, command_group_repository):
    group = integration_group_with_complete_data

    with unit_of_work:
        unit_of_work.groups.save(group)
        unit_of_work.commit()

    found_group = command_group_repository.group_of_id(id_=group.id(), tenant_id=group.tenant_id())

    assert found_group.is_deleted == group.is_deleted


def test_save__with_minimal_data(integration_group_with_minimal_data, unit_of_work, command_group_repository):
    group = integration_group_with_minimal_data

    with unit_of_work:
        unit_of_work.groups.save(group)
        unit_of_work.commit()

    found_group = command_group_repository.group_of_id(id_=group.id(), tenant_id=group.tenant_id())

    assert found_group is not None


def test_rollback(test_group_1, unit_of_work, command_group_repository):
    with unit_of_work:
        unit_of_work.groups.save(test_group_1)
        unit_of_work.rollback()

    found_group = command_group_repository.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())

    assert found_group is None


def test_tenant_isolation(integration_multi_tenant_groups, unit_of_work, command_group_repository):
    group_1, group_2 = integration_multi_tenant_groups

    with unit_of_work:
        unit_of_work.groups.save(group_1)
        unit_of_work.groups.save(group_2)
        unit_of_work.commit()

    found_1 = command_group_repository.group_of_id(id_=group_1.id(), tenant_id=group_1.tenant_id())
    found_2 = command_group_repository.group_of_id(id_=group_2.id(), tenant_id=group_2.tenant_id())

    cross_tenant = command_group_repository.group_of_id(id_=group_1.id(), tenant_id=group_2.tenant_id())

    assert found_1 is not None
    assert found_2 is not None
    assert cross_tenant is None


def test_sync_groups__new_groups__inserted(
    test_group_1,
    test_group_2,
    unit_of_work,
    command_group_repository,
):
    groups = [test_group_1, test_group_2]

    with unit_of_work:
        unit_of_work.groups.sync_groups(groups)
        unit_of_work.commit()

    found_1 = command_group_repository.group_of_id(id_=test_group_1.id(), tenant_id=test_group_1.tenant_id())
    found_2 = command_group_repository.group_of_id(id_=test_group_2.id(), tenant_id=test_group_2.tenant_id())

    assert found_1 is not None
    assert found_2 is not None
