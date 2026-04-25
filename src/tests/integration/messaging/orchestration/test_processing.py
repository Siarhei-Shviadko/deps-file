from deps_message_flow.sagas.testing_support import *

from deps_file.domain.model import ErrorCode, Status
from deps_file.messaging import Destination, ErrorType
from deps_file.messaging.orchestration import (
    PerformParsing,
    PerformParsingReply,
    PerformUnification,
)


def test_processing__success(
    suts, test_file_1_id, test_file_1_tenant_id, test_file_1, engine, parsing_features, language
):
    saga_data = suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    suts = (
        suts.expect()
        .command(
            PerformUnification(
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                document_type_id=None,
            )
        )
        .to(Destination.UNIFIER_SERVICE)
        .and_given()
        .success_reply()
        .expect()
        .command(
            PerformParsing(
                tenant_id=test_file_1_tenant_id(),
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                engine=engine,
                language=language,
                features=parsing_features,
            )
        )
        .to(Destination.PARSING_SERVICE)
        .and_given()
        .success_reply()
        .expect_completed_successfully()
    )

    saga_data = suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])


def test_processing__parsing_failure(
    suts,
    test_file_1_id,
    test_file_1_tenant_id,
    test_file_1,
    engine,
    parsing_features,
    language,
    error_message,
    command_file_repository,
):
    saga_data = suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    suts = (
        suts.expect()
        .command(
            PerformUnification(
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                document_type_id=None,
            )
        )
        .to(Destination.UNIFIER_SERVICE)
        .and_given()
        .success_reply()
        .expect()
        .command(
            PerformParsing(
                tenant_id=test_file_1_tenant_id(),
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                engine=engine,
                language=language,
                features=parsing_features,
            )
        )
        .to(Destination.PARSING_SERVICE)
        .and_given()
        .success_reply(PerformParsingReply(ErrorType.SYSTEM.value, error_message))
        .expect_completed_successfully()
    )

    saga_data = suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_PROCESSING


def test_processing__parsing_postponed(
    suts,
    test_file_1_id,
    test_file_1_tenant_id,
    test_file_1,
    engine,
    parsing_features,
    language,
    command_file_repository,
    error_message,
):
    saga_data = suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])

    suts = (
        suts.expect()
        .command(
            PerformUnification(
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                document_type_id=None,
            )
        )
        .to(Destination.UNIFIER_SERVICE)
        .and_given()
        .success_reply()
        .expect()
        .command(
            PerformParsing(
                tenant_id=test_file_1_tenant_id(),
                document_id=test_file_1_id(),
                files=[test_file_1.path],
                engine=engine,
                language=language,
                features=parsing_features,
            )
        )
        .to(Destination.PARSING_SERVICE)
        .and_given()
        .success_reply(PerformParsingReply(ErrorType.BUSINESS.value, error_message))
        .expect_completed_successfully()
    )

    saga_data = suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_PROCESSING
