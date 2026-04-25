from datetime import datetime
from uuid import uuid4

import pytest

from deps_file.domain.exceptions import (
    FileIsNotFailed,
    FileReferenceAlreadyExists,
    IllegalArgument,
)
from deps_file.domain.model.file import (
    ErrorCode,
    File,
    ProcessingParams,
    ReferenceType,
    Status,
    WorkflowParamsDict,
)
from tests.factories import FileFactory


def test_create__with_complete_data__created(
    test_file_1,
    test_file_1_id,
    tenant_id,
    file_name,
    file_path,
    test_processing_params_full,
):
    assert test_file_1.id() == test_file_1_id.value
    assert test_file_1.tenant_id() == tenant_id()
    assert test_file_1.name == file_name
    assert test_file_1.path == file_path
    assert test_file_1.processing_params == test_processing_params_full
    assert test_file_1.events == []
    assert test_file_1.labels
    assert len(test_file_1.labels) == 1
    [label] = test_file_1.labels
    assert label == "test_label"


def test_create__with_minimal_data__created(test_minimal_file):
    processing_params_min = ProcessingParams(
        group_id=None,
        splitting_enabled=False,
        classification_enabled=False,
        workflow_params=WorkflowParamsDict(
            document_type_id=None,
            parsing_features=[],
            needs_unifier=False,
            needs_extraction=False,
            assigned_to_me=False,
            llm_type=None,
            engine=None,
            language=None,
            metadata={},
        ),
    )

    assert test_minimal_file.name == "minimal_file.pdf"
    assert test_minimal_file.path == "/uploads/minimal_file.pdf"
    assert test_minimal_file.processing_params == processing_params_min
    assert test_minimal_file.id() is not None
    assert test_minimal_file.state.status == Status.PROCESSING
    assert isinstance(test_minimal_file.created_at, datetime)
    assert test_minimal_file.events == []
    assert not test_minimal_file.labels


def test_create__with_too_long_name__error(invalid_long_name):
    with pytest.raises(IllegalArgument):
        FileFactory(
            tenant_id=str(uuid4()),
            name=invalid_long_name,
            path="/uploads/test.pdf",
            processing_params=ProcessingParams(
                group_id=None,
                splitting_enabled=False,
                classification_enabled=False,
                workflow_params=WorkflowParamsDict(document_type_id=None),
            ),
        )


def test_create__with_too_long_path__error(invalid_long_path):
    with pytest.raises(IllegalArgument):
        FileFactory(
            tenant_id=str(uuid4()),
            name="test.pdf",
            path=invalid_long_path,
            processing_params=ProcessingParams(
                group_id=None,
                splitting_enabled=False,
                classification_enabled=False,
                workflow_params=WorkflowParamsDict(document_type_id=None),
            ),
        )


def test_classification_file__configured__has_classification_enabled(
    test_file_for_classification,
):
    params = test_file_for_classification.processing_params
    assert params.classification_enabled is True
    assert params.splitting_enabled is False
    assert params.group_id is not None


def test_processing_file__configured__has_processing_only(test_file_for_processing):
    params = test_file_for_processing.processing_params
    assert params.splitting_enabled is False
    assert params.classification_enabled is False


def test_minimal_file__configured__has_minimal_parameters(test_minimal_file):
    params = test_minimal_file.processing_params
    assert params.group_id is None
    assert params.splitting_enabled is False
    assert params.classification_enabled is False
    assert params.workflow_params["document_type_id"] is None


def test_set_reference__with_no_existing_reference__creates_reference(test_file_1):
    entity_id = str(uuid4())
    entity_name = "Test Document"

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )

    assert test_file_1.reference is not None
    assert test_file_1.reference.entity_type == ReferenceType.DOCUMENT
    assert test_file_1.reference.entity_id == entity_id
    assert test_file_1.reference.entity_name == entity_name


def test_set_reference__with_batch_type__creates_batch_reference(test_file_1):
    entity_id = str(uuid4())
    entity_name = "Test Batch"

    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=entity_id,
        entity_name=entity_name,
    )

    assert test_file_1.reference is not None
    assert test_file_1.reference.entity_type == ReferenceType.BATCH
    assert test_file_1.reference.entity_id == entity_id
    assert test_file_1.reference.entity_name == entity_name


def test_add_batch_reference__creates_batch_reference(test_file_1):
    entity_id = uuid4().hex
    entity_name = uuid4().hex

    test_file_1.add_batch_reference(entity_id=entity_id, entity_name=entity_name)

    assert test_file_1.reference is not None
    assert test_file_1.reference.entity_type == ReferenceType.BATCH
    assert test_file_1.reference.entity_id == entity_id
    assert test_file_1.reference.entity_name == entity_name


def test_set_reference__with_existing_reference__raises_error(test_file_1):
    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="First Document",
    )

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        test_file_1._add_reference(
            entity_type=ReferenceType.DOCUMENT,
            entity_id=str(uuid4()),
            entity_name="Second Document",
        )

    assert str(test_file_1.id()) in str(exc_info.value)


def test_complete_processing__ok(test_file_1: File):
    test_file_1.complete_processing()

    assert test_file_1.status == Status.COMPLETED
    assert test_file_1.state.error_message is None

    assert test_file_1.events is not None
    assert len(test_file_1.events) == 2
    assert test_file_1.events[-1].id == test_file_1.id()
    assert test_file_1.events[-1].status == Status.COMPLETED.value
    assert test_file_1.events[-1].error_message is None


def test_fail_processing__ok(test_file_1: File, error_message: str):
    test_file_1.fail_processing(error_message)

    assert test_file_1.status == Status.FAILED
    assert test_file_1.state.error_code == ErrorCode.FAIL_PROCESSING
    assert test_file_1.state.error_message == error_message

    assert test_file_1.events is not None
    assert len(test_file_1.events) == 2
    assert test_file_1.events[-1].id == test_file_1.id()
    assert test_file_1.events[-1].status == Status.FAILED.value
    assert test_file_1.events[-1].error_message == error_message


def test_complete_classification__ok(test_file_1: File, document_id, document_name):
    test_file_1.complete_classification(entity_id=document_id, entity_name=document_name)

    assert test_file_1.status == Status.COMPLETED
    assert test_file_1.state.error_message is None
    assert test_file_1.reference
    assert test_file_1.reference.entity_id == document_id
    assert test_file_1.reference.entity_name == document_name
    assert test_file_1.reference.entity_type == ReferenceType.DOCUMENT


def test_fail_classification__ok(test_file_1: File, error_message: str):
    test_file_1.fail_classification(error_message)

    assert test_file_1.status == Status.FAILED
    assert test_file_1.state.error_code == ErrorCode.FAIL_CLASSIFICATION

    assert test_file_1.state.error_message == error_message


def test_complete_splitting__ok(test_file_1: File, batch_id, batch_name):
    test_file_1.complete_splitting(entity_id=batch_id, entity_name=batch_name)

    assert test_file_1.status == Status.COMPLETED
    assert test_file_1.state.error_message is None
    assert test_file_1.reference
    assert test_file_1.reference.entity_id == batch_id
    assert test_file_1.reference.entity_name == batch_name
    assert test_file_1.reference.entity_type == ReferenceType.BATCH


def test_fail_splitting__ok(test_file_1: File, error_message: str):
    test_file_1.fail_splitting(error_message)

    assert test_file_1.status == Status.FAILED
    assert test_file_1.state.error_message == error_message
    assert test_file_1.state.error_code == ErrorCode.FAIL_SPLITTING


def test_classify__with_no_reference__updates_processing_params(test_file_1: File):
    group_id = str(uuid4())
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    original_processing_params = test_file_1.processing_params
    test_file_1.classify(group_id=group_id, workflow_params=workflow_params)

    assert test_file_1.processing_params.group_id() == group_id
    assert test_file_1.processing_params.workflow_params == workflow_params
    assert test_file_1.processing_params.splitting_enabled == original_processing_params.splitting_enabled
    assert test_file_1.processing_params.classification_enabled == original_processing_params.classification_enabled


def test_classify__with_document_reference__raises_file_reference_already_exists(test_file_1: File):
    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Existing Document",
    )

    group_id = str(uuid4())
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        test_file_1.classify(group_id=group_id, workflow_params=workflow_params)

    assert str(test_file_1.id()) in str(exc_info.value)
    assert exc_info.value.code == "file_reference_already_exists"


def test_classify__with_batch_reference__raises_file_reference_already_exists(test_file_1: File):
    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Existing Batch",
    )

    group_id = str(uuid4())
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        test_file_1.classify(group_id=group_id, workflow_params=workflow_params)

    assert str(test_file_1.id()) in str(exc_info.value)
    assert exc_info.value.code == "file_reference_already_exists"


def test_split__with_no_reference__updates_processing_params(test_file_1: File):
    group_id = str(uuid4())
    classification_enabled = True
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    original_processing_params = test_file_1.processing_params
    test_file_1.split(group_id=group_id, classification_enabled=classification_enabled, workflow_params=workflow_params)

    assert test_file_1.processing_params.group_id() == group_id
    assert test_file_1.processing_params.workflow_params == workflow_params
    assert test_file_1.processing_params.classification_enabled == classification_enabled
    assert test_file_1.processing_params.splitting_enabled == original_processing_params.splitting_enabled


def test_split__with_document_reference__raises_file_reference_already_exists(test_file_1: File):
    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Existing Document",
    )

    group_id = str(uuid4())
    classification_enabled = True
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        test_file_1.split(
            group_id=group_id, classification_enabled=classification_enabled, workflow_params=workflow_params
        )

    assert str(test_file_1.id()) in str(exc_info.value)
    assert exc_info.value.code == "file_reference_already_exists"


def test_split__with_batch_reference__raises_file_reference_already_exists(test_file_1: File):
    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Existing Batch",
    )

    group_id = str(uuid4())
    classification_enabled = True
    workflow_params = WorkflowParamsDict(
        document_type_id=str(uuid4()),
        engine="tesseract",
        language="eng",
        parsing_features=["text"],
        needs_unifier=True,
        needs_extraction=False,
        assigned_to_me=True,
        llm_type=None,
        metadata={},
    )

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        test_file_1.split(
            group_id=group_id, classification_enabled=classification_enabled, workflow_params=workflow_params
        )

    assert str(test_file_1.id()) in str(exc_info.value)
    assert exc_info.value.code == "file_reference_already_exists"


def test_restart__with_failed_file__updates_state(test_file_failed: File):
    test_file_failed.restart()

    assert test_file_failed.status == Status.PROCESSING
    assert test_file_failed.state.error_message is None


def test_restart__without_failed_file__raises_file_is_not_failed(test_file_1: File):
    with pytest.raises(FileIsNotFailed):
        test_file_1.restart()
