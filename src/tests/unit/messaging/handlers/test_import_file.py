import pytest

from deps_file.constants import COMMANDS_CHANNEL, COMMANDS_REPLIES_CHANNEL
from deps_file.domain.model import (
    ClassifyFileDomain,
    ProcessFileDomain,
    SplitFileDomain,
)
from deps_file.messaging.handlers import (
    import_file_for_classification_handler,
    import_file_for_processing_handler,
    import_file_for_splitting_handler,
)


def test_import_file__for_processing_handler(
    import_file_for_processing_command_message,
    command_file_service,
    fake_command_file_repository,
    fake_command_producer,
    tenant_id,
):
    import_file_for_processing_handler(command_message=import_file_for_processing_command_message)

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    result_file = fake_command_file_repository.file_of_id(command.file_id, tenant_id())

    assert result_file is not None
    assert result_file.tenant_id() == tenant_id()
    assert result_file.name == import_file_for_processing_command_message.command.file_name
    assert result_file.path == import_file_for_processing_command_message.command.file_path
    assert (
        result_file.processing_params.workflow_params
        == import_file_for_processing_command_message.command.workflow_params
    )

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ProcessFileDomain)
    assert command.tenant_id == tenant_id()
    assert command.files == [import_file_for_processing_command_message.command.file_path]
    assert (
        command.parsing_features
        == import_file_for_processing_command_message.command.workflow_params["parsing_features"]
    )
    assert command.engine == import_file_for_processing_command_message.command.workflow_params["engine"]
    assert command.language == import_file_for_processing_command_message.command.workflow_params["language"]


@pytest.mark.usefixtures("save_group")
def test_import_file__for_classification_handler(
    import_file_for_classification_command_message,
    command_file_service,
    fake_command_file_repository,
    fake_command_producer,
    tenant_id,
):
    import_file_for_classification_handler(command_message=import_file_for_classification_command_message)

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    result_file = fake_command_file_repository.file_of_id(command.file_id, tenant_id())

    assert result_file is not None
    assert result_file.tenant_id() == tenant_id()
    assert result_file.name == import_file_for_classification_command_message.command.file_name
    assert result_file.path == import_file_for_classification_command_message.command.file_path
    assert result_file.processing_params.group_id() == import_file_for_classification_command_message.command.group_id
    assert (
        result_file.processing_params.workflow_params
        == import_file_for_classification_command_message.command.workflow_params
    )

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ClassifyFileDomain)
    assert command.path == import_file_for_classification_command_message.command.file_path
    assert command.group_id == import_file_for_classification_command_message.command.group_id
    assert (
        command.parsing_features
        == import_file_for_classification_command_message.command.workflow_params["parsing_features"]
    )
    assert command.engine == import_file_for_classification_command_message.command.workflow_params["engine"]
    assert command.language == import_file_for_classification_command_message.command.workflow_params["language"]
    assert command.llm_type == import_file_for_classification_command_message.command.workflow_params["llm_type"]
    assert (
        command.needs_unifier == import_file_for_classification_command_message.command.workflow_params["needs_unifier"]
    )
    assert (
        command.needs_extraction
        == import_file_for_classification_command_message.command.workflow_params["needs_extraction"]
    )
    assert (
        command.assigned_to_me
        == import_file_for_classification_command_message.command.workflow_params["assigned_to_me"]
    )
    assert command.metadata == import_file_for_classification_command_message.command.workflow_params["metadata"]


@pytest.mark.usefixtures("save_group")
def test_import_file__for_splitting_handler(
    import_file_for_splitting_command_message,
    command_file_service,
    fake_command_file_repository,
    fake_command_producer,
    tenant_id,
):
    import_file_for_splitting_handler(command_message=import_file_for_splitting_command_message)

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    result_file = fake_command_file_repository.file_of_id(command.file_id, tenant_id())
    assert result_file is not None
    assert result_file.id() == command.file_id
    assert result_file.tenant_id() == tenant_id()
    assert result_file.name == import_file_for_splitting_command_message.command.file_name
    assert result_file.path == import_file_for_splitting_command_message.command.file_path
    assert result_file.processing_params.group_id() == import_file_for_splitting_command_message.command.group_id
    assert (
        result_file.processing_params.classification_enabled
        == import_file_for_splitting_command_message.command.classification_enabled
    )
    assert (
        result_file.processing_params.workflow_params
        == import_file_for_splitting_command_message.command.workflow_params
    )

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, SplitFileDomain)
    assert command.path == import_file_for_splitting_command_message.command.file_path
    assert command.group_id == import_file_for_splitting_command_message.command.group_id
    assert command.classification_enabled == import_file_for_splitting_command_message.command.classification_enabled
    assert (
        command.document_type_id
        == import_file_for_splitting_command_message.command.workflow_params["document_type_id"]
    )
    assert (
        command.parsing_features
        == import_file_for_splitting_command_message.command.workflow_params["parsing_features"]
    )
    assert command.engine == import_file_for_splitting_command_message.command.workflow_params["engine"]
    assert command.language == import_file_for_splitting_command_message.command.workflow_params["language"]
    assert command.llm_type == import_file_for_splitting_command_message.command.workflow_params["llm_type"]
    assert command.needs_unifier == import_file_for_splitting_command_message.command.workflow_params["needs_unifier"]
    assert (
        command.needs_extraction
        == import_file_for_splitting_command_message.command.workflow_params["needs_extraction"]
    )
    assert command.assigned_to_me == import_file_for_splitting_command_message.command.workflow_params["assigned_to_me"]
    assert command.metadata == import_file_for_splitting_command_message.command.workflow_params["metadata"]
