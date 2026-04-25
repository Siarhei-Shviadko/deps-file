from uuid import uuid4

from deps_message_flow.sagas.testing_support import *

from deps_file.domain.model import Status
from deps_file.messaging import Destination, ErrorType
from deps_file.messaging.orchestration import (
    PerformUnification,
    PerformUnificationReply,
)


def test_unification__success(suts, test_file_1_id, test_file_1):
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
    )

    saga_data = suts.saga_data
    assert Status.PROCESSING == Status(saga_data["current_status"])


def test_unification__failure(suts, test_file_1_id, test_file_1):
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
        .success_reply(PerformUnificationReply(ErrorType.SYSTEM.value, uuid4().hex))
    )
    saga_data = suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])


def test_unification__postponed(suts, test_file_1_id, test_file_1):
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
        .success_reply(PerformUnificationReply(ErrorType.BUSINESS.value, uuid4().hex))
        .expect_completed_successfully()
    )
    saga_data = suts.saga_data
    assert Status.FAILED == Status(saga_data["current_status"])
