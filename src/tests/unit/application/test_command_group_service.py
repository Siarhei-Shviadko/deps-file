from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from deps_file.application import CommandGroupService
from deps_file.domain.exceptions import GroupNotFound
from deps_file.domain.model import Group
from tests.factories import GroupFactory
from tests.fakes import FakeUnitOfWork
from tests.shared_fixtures.group import (
    test_group_1,
    test_group_1_id,
    test_group_1_tenant_id,
    test_group_2,
    test_group_2_id,
    test_group_2_tenant_id,
    test_group_minimal,
)


def test_create__valid_data__creates_and_returns_group(command_group_service, fake_unit_of_work_with_groups):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    result = command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    assert isinstance(result, Group)
    assert result.id() == group_id
    assert result.tenant_id() == tenant_id
    assert result.is_deleted is False


def test_create__commits_transaction(command_group_service, fake_unit_of_work_with_groups):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    saved_groups = fake_unit_of_work_with_groups.groups.get_saved_groups()
    assert len(saved_groups) == 1
    assert saved_groups[0].id() == group_id


def test_create__multiple_groups_same_tenant__creates_successfully(command_group_service):
    tenant_id = str(uuid4())

    group_1 = command_group_service.create(
        group_id=str(uuid4()),
        tenant_id=tenant_id,
    )

    group_2 = command_group_service.create(
        group_id=str(uuid4()),
        tenant_id=tenant_id,
    )

    assert group_1.tenant_id() == group_2.tenant_id()
    assert group_1.id() != group_2.id()


def test_delete__existing_group__soft_deletes_group(command_group_service, fake_unit_of_work_with_groups):
    group = GroupFactory.create_active()
    fake_unit_of_work_with_groups.groups.save(group)

    result = command_group_service.delete(
        group_id=group.id(),
        tenant_id=group.tenant_id(),
    )

    assert result.is_deleted is True
    deleted_groups = fake_unit_of_work_with_groups.groups.get_deleted_groups()
    assert len(deleted_groups) == 1


def test_delete__non_existing_group__raises_group_not_found(command_group_service):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    with pytest.raises(GroupNotFound):
        command_group_service.delete(
            group_id=group_id,
            tenant_id=tenant_id,
        )


def test_delete__wrong_tenant__raises_group_not_found(command_group_service, fake_unit_of_work_with_groups):
    group = GroupFactory.create_active()
    fake_unit_of_work_with_groups.groups.save(group)

    with pytest.raises(GroupNotFound):
        command_group_service.delete(
            group_id=group.id(),
            tenant_id=str(uuid4()),
        )


def test_uses_unit_of_work__for_transaction_management(
    fake_unit_of_work_with_groups,
    mock_command_producer,
    fake_domain_event_publisher,
    mock_group_proxy,
):
    service = CommandGroupService(
        unit_of_work=fake_unit_of_work_with_groups,
        command_producer=mock_command_producer,
        domain_event_publisher=fake_domain_event_publisher,
        group_proxy=mock_group_proxy,
    )

    group_id = str(uuid4())
    tenant_id = str(uuid4())

    service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    assert fake_unit_of_work_with_groups._in_transaction_calls > 0


def test_proper_logging__for_audit_trail(command_group_service, caplog):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    assert f"Group {group_id} is saved." in caplog.text


def test_delete_logging__for_audit_trail(command_group_service, fake_unit_of_work_with_groups, caplog):
    group = GroupFactory.create_active()
    fake_unit_of_work_with_groups.groups.save(group)

    command_group_service.delete(
        group_id=group.id(),
        tenant_id=group.tenant_id(),
    )

    assert f"Group {group.id()} is deleted." in caplog.text


def test_initialize__syncs_new_groups_from_api(
    command_group_service_with_groups,
    fake_unit_of_work_with_groups,
    mock_group_proxy,
    test_group_1,
    test_group_2,
):
    api_groups_data = [
        {
            "group_id": test_group_1.id(),
            "tenant_id": test_group_1.tenant_id(),
            "is_deleted": False,
        },
        {
            "group_id": test_group_2.id(),
            "tenant_id": test_group_2.tenant_id(),
            "is_deleted": False,
        },
    ]
    mock_group_proxy.get_all_groups.return_value = api_groups_data

    command_group_service_with_groups.initialize()
    groups_repo = fake_unit_of_work_with_groups.groups

    tenant1_group = groups_repo.group_of_id(test_group_1.id(), test_group_1.tenant_id())
    assert tenant1_group.id() == test_group_1.id()

    tenant2_group = groups_repo.group_of_id(test_group_2.id(), test_group_2.tenant_id())
    assert tenant2_group.id() == test_group_2.id()

    saved_groups = groups_repo.get_saved_groups()
    assert len(saved_groups) == 2


def test_initialize__updates_existing_groups(
    command_group_service_with_groups,
    fake_unit_of_work_with_groups,
    mock_group_proxy,
    test_group_minimal,
):
    groups_repo = fake_unit_of_work_with_groups.groups
    groups_repo.save(test_group_minimal)
    groups_repo.clear_calls()

    api_groups_data = [
        {
            "group_id": test_group_minimal.id(),
            "tenant_id": test_group_minimal.tenant_id(),
            "is_deleted": False,
        }
    ]
    mock_group_proxy.get_all_groups.return_value = api_groups_data

    command_group_service_with_groups.initialize()

    saved_group = groups_repo.group_of_id(test_group_minimal.id(), test_group_minimal.tenant_id())
    assert saved_group.id() == test_group_minimal.id()


def test_initialize__empty_response_is_valid(
    command_group_service_with_groups,
    fake_unit_of_work_with_groups,
    mock_group_proxy,
):
    mock_group_proxy.get_all_groups.return_value = []

    command_group_service_with_groups.initialize()

    groups_repo = fake_unit_of_work_with_groups.groups
    assert len(groups_repo.get_saved_groups()) == 0


def test_initialize__database_error_during_sync(
    command_group_service_with_groups,
    fake_unit_of_work_with_groups,
    mock_group_proxy,
    test_group_1,
    caplog,
):
    api_groups_data = [
        {
            "group_id": test_group_1.id(),
            "tenant_id": test_group_1.tenant_id(),
            "is_deleted": False,
        }
    ]
    mock_group_proxy.get_all_groups.return_value = api_groups_data

    fake_unit_of_work_with_groups.groups.sync_groups = MagicMock(side_effect=Exception("Database connection lost"))

    command_group_service_with_groups.initialize()

    assert "Failed to sync groups: Database connection lost" in caplog.text

    fake_unit_of_work_with_groups.groups.sync_groups.assert_called_once()
