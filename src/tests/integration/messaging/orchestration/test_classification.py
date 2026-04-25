from uuid import uuid4

from deps_message_flow.sagas.testing_support import *

from deps_file.constants import CLASSIFICATION_COMMANDS_CHANNEL
from deps_file.domain.model import ErrorCode, Status
from deps_file.messaging import ErrorType
from deps_file.messaging.orchestration.classification import (
    ClassifyFile,
    ClassifyFileReply,
)


def test_classification__success(
    classification_suts,
    test_file_1_id,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
):
    saga_data = classification_suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    document_id = uuid4().hex
    document_name = uuid4().hex
    document_type_id = uuid4().hex

    classification_suts = (
        classification_suts.expect()
        .command(
            ClassifyFile(
                file_id=test_file_1_id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
                start_processing=False,
            )
        )
        .to(CLASSIFICATION_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            ClassifyFileReply(
                file_id=test_file_1_id(),
                document_id=document_id,
                document_name=document_name,
                document_type_id=document_type_id,
                error_type=None,
                error_message=None,
            )
        )
        .expect_completed_successfully()
    )

    saga_data = classification_suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])
    assert saga_data["document_id"] == document_id
    assert saga_data["document_type_id"] == document_type_id
    assert saga_data["error_type"] is None
    assert saga_data["error_message"] is None


def test_classification__system_failure(
    classification_suts,
    test_file_1_id,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    error_message,
    command_file_repository,
):
    saga_data = classification_suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    error_message = uuid4().hex

    classification_suts = (
        classification_suts.expect()
        .command(
            ClassifyFile(
                file_id=test_file_1_id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
                start_processing=False,
            )
        )
        .to(CLASSIFICATION_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            ClassifyFileReply(
                file_id=test_file_1_id(),
                document_id="",
                document_name="",
                document_type_id="",
                error_type=ErrorType.SYSTEM.value,
                error_message=error_message,
            )
        )
        .expect_completed_successfully()
    )

    saga_data = classification_suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])
    assert saga_data["error_type"] == ErrorType.SYSTEM.value
    assert saga_data["error_message"] == error_message

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_CLASSIFICATION


def test_classification__business_failure(
    classification_suts,
    test_file_1_id,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    error_message,
    command_file_repository,
):
    saga_data = classification_suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    error_message = uuid4().hex

    classification_suts = (
        classification_suts.expect()
        .command(
            ClassifyFile(
                file_id=test_file_1_id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
                start_processing=False,
            )
        )
        .to(CLASSIFICATION_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            ClassifyFileReply(
                file_id=test_file_1_id(),
                document_id="",
                document_name="",
                document_type_id="",
                error_type=ErrorType.BUSINESS.value,
                error_message=error_message,
            )
        )
        .expect_completed_successfully()
    )

    saga_data = classification_suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])
    assert saga_data["error_type"] == ErrorType.BUSINESS.value
    assert saga_data["error_message"] == error_message

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_CLASSIFICATION
