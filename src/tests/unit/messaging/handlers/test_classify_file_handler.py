from unittest.mock import MagicMock

from deps_message_flow.commands.consumer.command_message import CommandMessage

from deps_file.domain.model.file.commands import ClassifyFileDomain
from deps_file.messaging.handlers import classify_file_handler


def test_classify_file_handler__passes_needs_unifier_and_needs_extraction(
    test_file_1,
    mock_saga_file_service,
    test_group_1_tenant_id,
):
    command = ClassifyFileDomain(
        file_id=str(test_file_1.id()),
        file_name=test_file_1.name,
        path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        engine="test-engine",
        language="en",
        parsing_features=["tables"],
        llm_type="gpt-4",
        needs_unifier=True,
        needs_extraction=True,
        metadata={"key": "value"},
    )

    message = MagicMock()
    command_message = CommandMessage(
        message_id="test-message-id",
        command=command,
        correlation_headers={},
        message=message,
    )

    classify_file_handler(
        command_message=command_message,
        tenant_id=test_group_1_tenant_id,
        saga_file_service=mock_saga_file_service,
    )

    call_kwargs = mock_saga_file_service.classify_file.call_args.kwargs
    assert call_kwargs["needs_unifier"] is True
    assert call_kwargs["needs_extraction"] is True
