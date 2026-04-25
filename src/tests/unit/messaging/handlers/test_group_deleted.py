import pytest

from deps_file.messaging.handlers import group_deleted_handler


@pytest.mark.usefixtures("save_group")
def test_group_deleted__marks_as_deleted(
    group_deleted_dee,
    command_group_service,
    fake_unit_of_work_with_groups,
    test_group_1,
):
    initial_group = fake_unit_of_work_with_groups.groups.group_of_id(test_group_1.id(), test_group_1.tenant_id())
    assert initial_group is not None

    group_deleted_handler(dee=group_deleted_dee, group_service=command_group_service)

    result_group = fake_unit_of_work_with_groups.groups.group_of_id(test_group_1.id(), test_group_1.tenant_id())
    assert result_group is None

    all_groups = fake_unit_of_work_with_groups.groups.get_all_groups_including_deleted(test_group_1.tenant_id())
    deleted_group = next((g for g in all_groups if g.id() == test_group_1.id()), None)
    assert deleted_group is not None
    assert deleted_group.is_deleted
