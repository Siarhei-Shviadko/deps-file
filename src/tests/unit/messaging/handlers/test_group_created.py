from deps_file.messaging.handlers import group_created_handler


def test_group_created__creates_group(
    group_created_dee,
    command_group_service,
    fake_unit_of_work_with_groups,
    test_group_1,
):
    group_created_handler(dee=group_created_dee, group_service=command_group_service)

    result_group = fake_unit_of_work_with_groups.groups.group_of_id(test_group_1.id(), test_group_1.tenant_id())
    assert result_group is not None
    assert result_group.id() == test_group_1.id()
    assert result_group.tenant_id() == test_group_1.tenant_id()
