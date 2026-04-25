import pytest

from deps_file.domain.model.file.state import State, Status
from tests.factories.file_state_factory import StateFactory


def test_create__with_processing_status__created():
    state = StateFactory.processing()

    assert state.status == "processing"
    assert state.error_message is None


def test_create__with_completed_status__created():
    state = StateFactory.completed()

    assert state.status == "completed"
    assert state.error_message is None


def test_create__with_failed_status_and_error__created():
    error_msg = "File processing failed"
    state = StateFactory.failed(error_message=error_msg)

    assert state.status == "failed"
    assert state.error_message == error_msg


def test_create__with_default_failed_error__has_default_message():
    state = StateFactory.failed()

    assert state.status == "failed"
    assert state.error_message == "Processing failed"


def test_create__with_string_status__created():
    state = StateFactory.processing()

    assert state.status == "processing"
    assert state.error_message is None


def test_create__with_invalid_status__error():
    with pytest.raises(ValueError, match="Invalid status: invalid"):
        StateFactory(status="invalid")


def test_equality__different_status__not_equal():
    state1 = StateFactory.processing()
    state2 = StateFactory.completed()

    assert state1 != state2


def test_equality__same_status_different_error__not_equal():
    state1 = StateFactory.failed(error_message="Error 1")
    state2 = StateFactory.failed(error_message="Error 2")

    assert state1 != state2


def test_equality__different_type__not_equal():
    state = StateFactory.processing()

    assert state != "processing"
    assert state != {"status": "processing"}


def test_factory__with_custom_attributes__overrides_defaults():
    custom_error = "Custom error message"
    state = StateFactory(status=Status.COMPLETED, error_message=custom_error)

    assert state.status == "completed"
    assert state.error_message == custom_error
