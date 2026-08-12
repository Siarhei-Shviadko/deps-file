import pytest

from deps_file.domain.model.file import Status
from deps_file.messaging.handlers import split_file_executed_handler


@pytest.mark.usefixtures("save_test_file_for_splitting", "save_group")
def test_split_file_executed_handler__success__completes_splitting(
    split_file_executed_envelope,
    command_file_service,
    fake_command_file_repository,
    tenant_id,
):
    split_file_executed_handler(split_file_executed_envelope)

    file = fake_command_file_repository.file_of_id(split_file_executed_envelope.event.file_id, tenant_id())
    assert file.status == Status.COMPLETED
    assert file.reference is not None
    assert file.reference.entity_id == split_file_executed_envelope.event.batch_id


@pytest.mark.usefixtures("save_test_file_for_splitting", "save_group")
def test_split_file_executed_handler__failure__fails_splitting(
    split_file_executed_failure_envelope,
    command_file_service,
    fake_command_file_repository,
    tenant_id,
):
    split_file_executed_handler(split_file_executed_failure_envelope)

    file = fake_command_file_repository.file_of_id(split_file_executed_failure_envelope.event.file_id, tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == split_file_executed_failure_envelope.event.error_message
