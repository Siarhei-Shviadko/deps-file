from uuid import uuid4

import pytest
from faker.proxy import Faker

from deps_file.domain.model import FileId
from deps_file.domain.model.file import File, ProcessingParams, WorkflowParamsDict
from deps_file.domain.model.file.constants import (
    MAX_FILE_NAME_LENGTH,
    MAX_FILE_PATH_LENGTH,
)
from deps_file.domain.model.file.state import State, Status
from deps_file.domain.model.shared import TenantId
from tests.factories import FileFactory

__all__ = [
    "test_file_1_id",
    "test_file_1_tenant_id",
    "test_file_2_id",
    "test_file_2_tenant_id",
    "test_workflow_params",
    "test_workflow_params_none",
    "test_processing_params_full",
    "test_processing_params_minimal",
    "test_file_1",
    "test_file_2",
    "test_minimal_file",
    "test_file_for_splitting",
    "test_file_for_classification",
    "test_file_for_processing",
    "invalid_long_name",
    "invalid_long_path",
    "valid_max_name",
    "valid_max_path",
    "error_message",
    "document_id",
    "document_name",
    "batch_id",
    "batch_name",
]


@pytest.fixture
def test_file_1_id() -> FileId:
    return FileId()


@pytest.fixture
def test_file_1_tenant_id() -> TenantId:
    return TenantId()


@pytest.fixture
def test_file_2_id() -> FileId:
    return FileId()


@pytest.fixture
def test_file_2_tenant_id() -> TenantId:
    return TenantId()


@pytest.fixture
def test_workflow_params() -> WorkflowParamsDict:
    return WorkflowParamsDict(
        document_type_id=str(uuid4()),
        parsing_features=[],
        needs_unifier=False,
        needs_extraction=False,
        assigned_to_me=False,
        llm_type=None,
        engine=None,
        language=None,
        metadata={},
    )


@pytest.fixture
def test_workflow_params_none() -> WorkflowParamsDict:
    return WorkflowParamsDict(
        needs_unifier=False,
        needs_extraction=False,
        assigned_to_me=False,
        metadata={},
    )


@pytest.fixture
def test_processing_params_full(test_workflow_params, test_group_1_id) -> ProcessingParams:
    return ProcessingParams(
        group_id=test_group_1_id(),
        splitting_enabled=True,
        classification_enabled=True,
        workflow_params=test_workflow_params,
    )


@pytest.fixture
def test_processing_params_minimal(
    test_workflow_params_none,
) -> ProcessingParams:
    return ProcessingParams(
        group_id=None,
        splitting_enabled=False,
        classification_enabled=False,
        workflow_params=test_workflow_params_none,
    )


@pytest.fixture
def test_file_1(test_file_1_id, tenant_id, test_processing_params_full, file_name, file_path) -> File:
    file = FileFactory(
        id_=test_file_1_id(),
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        state=State(Status.PROCESSING),
        processing_params=test_processing_params_full,
        labels=["test_label"],
    )
    file.events.clear()
    return file


@pytest.fixture
def test_file_2(test_file_2_id, test_file_2_tenant_id) -> File:
    file = FileFactory(
        id_=test_file_2_id(),
        tenant_id=test_file_2_tenant_id(),
        name="another_document.docx",
        path="/uploads/tenant_2/another_document.docx",
        state=State(Status.COMPLETED),
        labels=[uuid4().hex for _ in range(5)],
    )
    file.events.clear()
    return file


@pytest.fixture
def test_minimal_file() -> File:
    file = FileFactory.create_with_minimal_data()
    file.events.clear()
    return file


@pytest.fixture
def test_file_for_splitting(
    tenant_id,
    file_name,
    file_path,
    test_workflow_params,
    test_group_1_id,
) -> File:
    file = FileFactory.create_for_splitting(
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        group_id=test_group_1_id(),
        classification_enabled=True,
        workflow_params=test_workflow_params,
    )
    file.events.clear()
    return file


@pytest.fixture
def test_file_for_classification(
    tenant_id,
    file_name,
    file_path,
    test_workflow_params,
    test_group_1_id,
) -> File:
    file = FileFactory.create_for_classification(
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        group_id=test_group_1_id(),
        workflow_params=test_workflow_params,
    )
    file.events.clear()
    return file


@pytest.fixture
def test_file_for_processing(
    tenant_id,
    file_name,
    file_path,
    test_workflow_params,
) -> File:
    file = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        workflow_params=test_workflow_params,
    )
    file.events.clear()
    return file


@pytest.fixture
def test_file_failed(test_file_1, error_message) -> File:
    test_file_1.fail_processing(error_message)
    return test_file_1


@pytest.fixture
def invalid_long_name() -> str:
    return "a" * (MAX_FILE_NAME_LENGTH + 1)


@pytest.fixture
def invalid_long_path() -> str:
    return "/" + "a" * MAX_FILE_PATH_LENGTH


@pytest.fixture
def valid_max_name() -> str:
    return "a" * MAX_FILE_NAME_LENGTH


@pytest.fixture
def valid_max_path() -> str:
    return "/" + "a" * (MAX_FILE_PATH_LENGTH - 1)


@pytest.fixture
def error_message(faker: Faker) -> str:
    return faker.text(20)


@pytest.fixture
def document_id() -> str:
    return uuid4().hex


@pytest.fixture
def document_name(faker: Faker) -> str:
    return faker.file_name(extension="pdf")


@pytest.fixture
def file_name(faker: Faker) -> str:
    return faker.file_name(extension="pdf")


@pytest.fixture
def file_path(faker: Faker) -> str:
    return faker.file_name(extension="pdf")


@pytest.fixture
def batch_id() -> str:
    return uuid4().hex


@pytest.fixture
def batch_name(faker: Faker) -> str:
    return faker.word()


@pytest.fixture
def save_file(fake_unit_of_work, test_file_1) -> None:
    fake_unit_of_work.files.save(test_file_1)


@pytest.fixture
def test_file_1_content(faker: Faker) -> bytes:
    return faker.json_bytes()


@pytest.fixture
def save_test_file_1_content(fake_object_storage, test_file_1, test_file_1_content) -> None:
    fake_object_storage.upload(test_file_1.path, test_file_1_content, replace_if_exists=True)


@pytest.fixture
def save_test_file_for_processing(fake_unit_of_work, test_file_for_processing) -> None:
    fake_unit_of_work.files.save(test_file_for_processing)


@pytest.fixture
def save_test_file_for_classification(fake_unit_of_work, test_file_for_classification) -> None:
    fake_unit_of_work.files.save(test_file_for_classification)


@pytest.fixture
def save_test_file_for_splitting(fake_unit_of_work, test_file_for_splitting) -> None:
    fake_unit_of_work.files.save(test_file_for_splitting)


@pytest.fixture
def save_test_failed_file_for_processing(fake_unit_of_work, test_file_for_processing, error_message) -> None:
    test_file_for_processing.fail_processing(error_message)
    fake_unit_of_work.files.save(test_file_for_processing)


@pytest.fixture
def save_test_failed_file_for_classification(fake_unit_of_work, test_file_for_classification, error_message) -> None:
    test_file_for_classification.fail_classification(error_message)
    fake_unit_of_work.files.save(test_file_for_classification)


@pytest.fixture
def save_test_failed_file_for_splitting(fake_unit_of_work, test_file_for_splitting, error_message) -> None:
    test_file_for_splitting.fail_splitting(error_message)
    fake_unit_of_work.files.save(test_file_for_splitting)
