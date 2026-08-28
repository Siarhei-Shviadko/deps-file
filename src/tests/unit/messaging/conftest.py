from unittest.mock import MagicMock

import pytest
from deps_message_flow.commands.consumer.command_message import CommandMessage
from deps_message_flow.events.subscriber.domain_event_envelope import (
    DomainEventEnvelope,
)

from deps_file.domain.model.file.commands import ClassifyFileDomain
from deps_file.messaging.commands import (
    DeleteFile,
    ImportFileForClassification,
    ImportFileForProcessing,
    ImportFileForSplitting,
)
from deps_file.messaging.events import (
    SplitFileExecuted,
    SplittingProposalAwaitingReview,
)


@pytest.fixture
def group_created_event(test_group_1):
    event = MagicMock()
    event.id = test_group_1.id()
    event.tenant_id = test_group_1.tenant_id()
    return event


@pytest.fixture
def group_deleted_event(test_group_1):
    event = MagicMock()
    event.id = test_group_1.id()
    event.tenant_id = test_group_1.tenant_id()
    return event


@pytest.fixture
def group_created_dee(group_created_event):
    dee = MagicMock(spec=DomainEventEnvelope)
    dee.event = group_created_event
    return dee


@pytest.fixture
def group_deleted_dee(group_deleted_event):
    dee = MagicMock(spec=DomainEventEnvelope)
    dee.event = group_deleted_event
    return dee


@pytest.fixture
def import_file_for_processing_command(test_file_1, test_workflow_params):
    return ImportFileForProcessing(
        file_name=test_file_1.name,
        file_path=test_file_1.path,
        workflow_params=test_workflow_params,
    )


@pytest.fixture
def import_file_for_processing_command_message(mocker, import_file_for_processing_command):
    cm = mocker.Mock(CommandMessage)
    cm.command = import_file_for_processing_command

    return cm


@pytest.fixture
def import_file_for_classification_command(test_file_1):
    return ImportFileForClassification(
        file_name=test_file_1.name,
        file_path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        workflow_params=test_file_1.processing_params.workflow_params,
    )


@pytest.fixture
def import_file_for_classification_command_message(mocker, import_file_for_classification_command):
    cm = mocker.Mock(CommandMessage)
    cm.command = import_file_for_classification_command

    return cm


@pytest.fixture
def import_file_for_splitting_command(test_file_1):
    return ImportFileForSplitting(
        file_name=test_file_1.name,
        file_path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        classification_enabled=test_file_1.processing_params.classification_enabled,
        workflow_params=test_file_1.processing_params.workflow_params,
    )


@pytest.fixture
def import_file_for_splitting_command_message(mocker, import_file_for_splitting_command):
    cm = mocker.Mock(CommandMessage)
    cm.command = import_file_for_splitting_command

    return cm


@pytest.fixture
def classify_file_command(test_file_1):
    return ClassifyFileDomain(
        file_id=str(test_file_1.id()),
        file_name=test_file_1.name,
        path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        engine=test_file_1.processing_params.workflow_params.get("engine"),
        language=test_file_1.processing_params.workflow_params.get("language"),
        parsing_features=test_file_1.processing_params.workflow_params.get("parsing_features"),
        llm_type=test_file_1.processing_params.workflow_params.get("llm_type"),
        needs_unifier=test_file_1.processing_params.workflow_params.get("needs_unifier", False),
        needs_extraction=test_file_1.processing_params.workflow_params.get("needs_extraction", False),
        metadata=test_file_1.processing_params.workflow_params.get("metadata"),
    )


@pytest.fixture
def classify_file_command_message(classify_file_command):
    message = MagicMock()
    command_message = CommandMessage(
        message_id="test-message-id",
        command=classify_file_command,
        correlation_headers={},
        message=message,
    )
    return command_message


@pytest.fixture
def mock_saga_file_service(mocker, containers):
    with containers.saga_file_service.override(mocker.Mock(containers.saga_file_service.cls)) as msfs:
        yield msfs()


@pytest.fixture
def split_file_cm(mocker, split_file_command):
    cm = mocker.Mock(CommandMessage)
    cm.command = split_file_command

    return cm


@pytest.fixture
def delete_file_command_message(mocker, test_file_1, test_file_2):
    cm = mocker.Mock(CommandMessage)
    cm.command = DeleteFile(file_ids=[str(test_file_1.id()), str(test_file_2.id())])

    return cm


@pytest.fixture
def split_file_executed_envelope(mocker, test_file_for_splitting):
    dee = mocker.Mock(DomainEventEnvelope)
    dee.event = SplitFileExecuted(
        file_id=test_file_for_splitting.id(),
        batch_id="batch_123",
        batch_name="123",
        error_type=None,
        error_message=None,
    )

    return dee


@pytest.fixture
def split_file_executed_failure_envelope(mocker, test_file_for_splitting):
    dee = mocker.Mock(DomainEventEnvelope)
    dee.event = SplitFileExecuted(
        file_id=test_file_for_splitting.id(),
        batch_id=None,
        batch_name=None,
        error_type="processing_error",
        error_message="splitting failed",
    )

    return dee


@pytest.fixture
def splitting_proposal_awaiting_review_envelope(mocker, test_file_for_splitting):
    dee = mocker.Mock(DomainEventEnvelope)
    dee.event = SplittingProposalAwaitingReview(test_file_for_splitting.id())

    return dee
