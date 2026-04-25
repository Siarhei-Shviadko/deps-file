from datetime import datetime
from uuid import uuid4

import pytest

from deps_file.domain.exceptions import IllegalArgument
from deps_file.domain.model.file import (
    File,
    FileFactory,
    FileId,
    ProcessingParamsDict,
    WorkflowParamsDict,
)
from deps_file.domain.model.file.events import FileCreated
from deps_file.domain.model.file.state import State, Status
from deps_file.domain.model.shared import TenantId
from tests.shared_fixtures.file import test_workflow_params


def test_create_for_splitting__with_full_data__created(splitting_file_full_data, test_workflow_params):
    file = splitting_file_full_data

    assert isinstance(file, File)
    assert file.name == "splitting_test.pdf"
    assert file.path == "/uploads/splitting_test.pdf"
    assert file.state.status == Status.PROCESSING
    assert file.processing_params.splitting_enabled is True
    assert file.processing_params.classification_enabled is True
    assert file.processing_params.group_id is not None
    assert file.processing_params.workflow_params == test_workflow_params
    assert isinstance(file.created_at, datetime)
    assert isinstance(file.updated_at, datetime)
    assert file.created_at == file.updated_at
    assert len(file.events) == 1
    assert isinstance(file.events[0], FileCreated)


def test_create_for_splitting__classification_disabled__has_splitting_only(splitting_file_no_classification):
    params = splitting_file_no_classification.processing_params
    assert params.splitting_enabled is True
    assert params.classification_enabled is False
    assert params.group_id is not None


def test_create_for_splitting__minimal_data__created(splitting_file_minimal_data):
    params = splitting_file_minimal_data.processing_params
    assert params.workflow_params["document_type_id"] is None
    assert params.splitting_enabled is True


def test_create_for_classification__with_full_data__created(classification_file_full_data, test_workflow_params):
    file = classification_file_full_data

    assert isinstance(file, File)
    assert file.name == "classification_test.pdf"
    assert file.path == "/uploads/classification_test.pdf"
    assert file.state.status == Status.PROCESSING
    params = file.processing_params
    assert params.splitting_enabled is False
    assert params.classification_enabled is True
    assert params.group_id is not None
    assert params.workflow_params == test_workflow_params
    assert len(file.events) == 1
    assert isinstance(file.events[0], FileCreated)


def test_create_for_classification__minimal_data__created(classification_file_minimal_data):
    params = classification_file_minimal_data.processing_params
    assert params.workflow_params["document_type_id"] is None
    assert params.classification_enabled is True
    assert params.splitting_enabled is False


def test_create_for_processing__with_full_data__created(processing_file_full_data, test_workflow_params):
    file = processing_file_full_data

    assert isinstance(file, File)
    assert file.name == "processing_test.pdf"
    assert file.path == "/uploads/processing_test.pdf"
    assert file.state.status == Status.PROCESSING
    assert file.processing_params.group_id is not None
    assert file.processing_params.splitting_enabled is False
    assert file.processing_params.classification_enabled is False
    assert file.processing_params.workflow_params == test_workflow_params
    assert len(file.events) == 1
    assert isinstance(file.events[0], FileCreated)


def test_create_for_processing__no_group__created(processing_file_no_group):
    assert processing_file_no_group.processing_params.group_id is None
    assert processing_file_no_group.processing_params.splitting_enabled is False
    assert processing_file_no_group.processing_params.classification_enabled is False


def test_create_for_processing__minimal_data__created(processing_file_minimal_data):
    assert processing_file_minimal_data.processing_params.workflow_params["document_type_id"] is None
    assert processing_file_minimal_data.processing_params.group_id is None


def test_factory_methods__create_processing_state__all_processing(factory_files_for_state_testing):
    splitting_file, classification_file, processing_file = factory_files_for_state_testing

    assert splitting_file.state.status == Status.PROCESSING
    assert classification_file.state.status == Status.PROCESSING
    assert processing_file.state.status == Status.PROCESSING


def test_factory_methods__generate_unique_ids__all_unique(factory_files_for_id_testing):
    file_1, file_2, file_3 = factory_files_for_id_testing

    assert file_1.id() != file_2.id()
    assert file_2.id() != file_3.id()
    assert file_1.id() != file_3.id()


def test_factory_methods__set_timestamps__valid_timestamps(splitting_file_full_data):
    file = splitting_file_full_data

    assert isinstance(file.created_at, datetime)
    assert isinstance(file.updated_at, datetime)
    assert file.created_at == file.updated_at


def test_factory_methods__create_file_created_event__has_event(factory_files_for_state_testing):
    splitting_file, classification_file, processing_file = factory_files_for_state_testing

    files = [splitting_file, classification_file, processing_file]

    for file in files:
        assert len(file.events) == 1
        event = file.events[0]
        assert isinstance(event, FileCreated)
        assert event.file_id == file.id()
        assert event.name == file.name
        assert event.path == file.path
        assert event.processing_params == ProcessingParamsDict(
            group_id=file.processing_params.group_id() if file.processing_params.group_id else None,
            splitting_enabled=file.processing_params.splitting_enabled,
            classification_enabled=file.processing_params.splitting_enabled,
            workflow_params=file.processing_params.workflow_params,  # type: ignore
        )


@pytest.mark.parametrize(
    "field,value,error_pattern",
    [
        ("name", "", "Attribute name.*cannot be less than 1"),
        ("path", "", "Attribute path.*cannot be less than 1"),
        ("name", "x" * 256, "Attribute name.*cannot be more than 255"),
        ("path", "x" * 1001, "Attribute path.*cannot be more than 1000"),
    ],
)
def test_file_field_validation(field, value, error_pattern):
    params = {
        "tenant_id": TenantId().value,
        "name": "valid.pdf",
        "path": "/valid/path.pdf",
        "group_id": str(uuid4()),
        "workflow_params": WorkflowParamsDict(document_type_id=str(uuid4())),
        field: value,
    }

    with pytest.raises(IllegalArgument, match=error_pattern):
        FileFactory.create_for_processing(**params)


def test_factory__with_none_values__accepted(factory_file_with_none_values):
    file = factory_file_with_none_values

    assert file.processing_params.group_id is None
    assert file.processing_params.workflow_params["document_type_id"] is None


def test_create_for_classification__with_labels__creates_file_labels():
    tenant_id = str(uuid4())
    labels = ["label1", "label2", "label3"]

    file = FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name="test_file.pdf",
        path="/uploads/test_file.pdf",
        group_id=str(uuid4()),
        workflow_params=WorkflowParamsDict(document_type_id=str(uuid4())),
        labels=labels,
    )

    assert file.labels is not None
    assert len(file.labels) == 3
    assert file.labels == labels


def test_create_for_classification__without_labels__creates_file_without_labels():
    tenant_id = str(uuid4())

    file = FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name="test_file.pdf",
        path="/uploads/test_file.pdf",
        group_id=str(uuid4()),
        workflow_params=WorkflowParamsDict(document_type_id=str(uuid4())),
        labels=None,
    )

    assert file.labels is None


def test_create_for_splitting__with_labels__creates_file_labels():
    tenant_id = str(uuid4())
    labels = ["split_label1", "split_label2"]

    file = FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name="split_file.pdf",
        path="/uploads/split_file.pdf",
        group_id=str(uuid4()),
        classification_enabled=True,
        workflow_params=WorkflowParamsDict(document_type_id=str(uuid4())),
        labels=labels,
    )

    assert file.labels is not None
    assert len(file.labels) == 2
    assert file.labels == labels
