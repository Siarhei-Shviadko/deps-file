from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from deps_file.application import CommandGroupService
from deps_file.application.file import CommandFileService, QueryFileService
from deps_file.domain.model import FileFactory, WorkflowParamsDict
from tests.fakes import (
    FakeCommandFileRepository,
    FakeCommandGroupRepository,
    FakeCommandProducer,
    FakeCommandUserRepository,
    FakeQueryFileRepository,
    FakeUnitOfWork,
)

pytest_plugins = [
    "tests.shared_fixtures.file.endpoints_fixtures",
    "tests.shared_fixtures.file.file_fixtures",
    "tests.shared_fixtures.group.group_fixtures",
]


@pytest.fixture(autouse=True)
def mock_query_file_service_autouse(app, mocker):
    svc = mocker.Mock()
    svc.find_all_with.return_value = {
        "files": [],
        "result_set": {"count": 0, "total": 0},
    }
    app.containers.query_file_service.override(svc)

    yield svc

    app.containers.query_file_service.reset_override()


@pytest.fixture
def postgres_session_mock(mocker, containers):
    mock = mocker.Mock()
    containers.datasources.postgres_session.override(mock)

    yield mock

    containers.datasources.postgres_session.reset_override()


@pytest.fixture
def fake_command_file_repository():
    return FakeCommandFileRepository()


@pytest.fixture(autouse=True)
def fake_unit_of_work(
    containers,
    test_users,
    fake_command_file_repository,
    fake_command_group_repository,
):
    fuow = FakeUnitOfWork(
        users=FakeCommandUserRepository(users=test_users),
        files=fake_command_file_repository,
        groups=fake_command_group_repository,
    )

    containers.unit_of_work.override(fuow)

    yield fuow

    containers.unit_of_work.reset_override()


@pytest.fixture(autouse=True)
def query_file_repository(repositories):
    fake_repo = FakeQueryFileRepository()
    with repositories.query_file.override(fake_repo):
        yield fake_repo


@pytest.fixture
def query_file_service(query_file_repository):
    return QueryFileService(query_file_repository=query_file_repository)


@pytest.fixture
def command_file_service(
    query_file_repository,
    fake_unit_of_work,
    containers,
    fake_command_producer,
    object_storage_mock,
    fake_document_proxy,
    fake_batch_proxy,
    fake_domain_event_publisher,
):
    service = CommandFileService(
        object_storage=object_storage_mock,
        unit_of_work=fake_unit_of_work,
        domain_event_publisher=fake_domain_event_publisher,
        document_proxy=fake_document_proxy,
        batch_proxy=fake_batch_proxy,
        command_producer=fake_command_producer,
    )

    containers.command_file_service.override(service)

    yield service

    containers.command_file_service.reset_override()


@pytest.fixture
def fake_command_group_repository():
    return FakeCommandGroupRepository()


@pytest.fixture
def test_file_and_group_setup(fake_unit_of_work, test_file_1, test_group_1):
    file_id = test_file_1.id()
    tenant_id = test_file_1.tenant_id()
    group_id = test_group_1.id()

    fake_unit_of_work.files._db[(file_id, tenant_id)] = test_file_1
    fake_unit_of_work.groups._db[(group_id, tenant_id)] = test_group_1

    return {
        "file_id": file_id,
        "tenant_id": tenant_id,
        "group_id": group_id,
    }


@pytest.fixture
def fake_unit_of_work_with_groups(fake_command_group_repository):
    return FakeUnitOfWork(groups=fake_command_group_repository)


@pytest.fixture
def mock_command_producer():
    return Mock()


@pytest.fixture
def fake_command_producer():
    return FakeCommandProducer()


@pytest.fixture
def mock_group_proxy():
    return MagicMock()


@pytest.fixture
def basic_classify_params():
    return {
        "tenant_id": "test_tenant",
        "name": "test.pdf",
        "content": b"content",
        "group_id": "valid_group_id",
        "workflow_params": {"document_type_id": "test-doc-type-id"},
        "labels": [],
    }


@pytest.fixture
def basic_split_params():
    return {
        "document_type_id": str(uuid4()),
        "parsing_features": [],
        "needs_unifier": True,
        "needs_extraction": True,
        "assigned_to_me": True,
        "llm_type": None,
        "engine": None,
        "language": None,
        "metadata": {},
    }


@pytest.fixture
def command_group_service(
    fake_unit_of_work,
    fake_command_producer,
    fake_domain_event_publisher,
    mock_group_proxy,
):
    return CommandGroupService(
        unit_of_work=fake_unit_of_work,
        command_producer=fake_command_producer,
        domain_event_publisher=fake_domain_event_publisher,
        group_proxy=mock_group_proxy,
    )


@pytest.fixture
def command_group_service_with_groups(
    fake_unit_of_work_with_groups,
    mock_command_producer,
    mock_group_proxy,
):
    def sync_groups(self, groups):
        for group in groups:
            self.save(group)

    fake_unit_of_work_with_groups.groups.sync_groups = sync_groups.__get__(
        fake_unit_of_work_with_groups.groups,
        type(fake_unit_of_work_with_groups.groups),
    )

    return CommandGroupService(
        unit_of_work=fake_unit_of_work_with_groups,
        command_producer=mock_command_producer,
        domain_event_publisher=MagicMock(),
        group_proxy=mock_group_proxy,
    )


@pytest.fixture
def splitting_file_full_data(test_workflow_params):
    tenant_id = str(uuid4())
    name = "splitting_test.pdf"
    path = "/uploads/splitting_test.pdf"
    group_id = str(uuid4())

    return FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        classification_enabled=True,
        workflow_params=test_workflow_params,
        labels=None,
    )


@pytest.fixture
def splitting_file_no_classification():
    tenant_id = str(uuid4())
    workflow_params = WorkflowParamsDict(document_type_id=str(uuid4()))

    return FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name="splitting_no_classification.pdf",
        path="/uploads/splitting_no_classification.pdf",
        group_id=str(uuid4()),
        classification_enabled=False,
        workflow_params=workflow_params,
        labels=None,
    )


@pytest.fixture
def splitting_file_minimal_data():
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    workflow_params = WorkflowParamsDict(document_type_id=None)

    return FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name="minimal_splitting.pdf",
        path="/uploads/minimal_splitting.pdf",
        group_id=group_id,
        classification_enabled=False,
        workflow_params=workflow_params,
        labels=None,
    )


@pytest.fixture
def classification_file_full_data(test_workflow_params):
    tenant_id = str(uuid4())
    name = "classification_test.pdf"
    path = "/uploads/classification_test.pdf"
    group_id = str(uuid4())

    return FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
        labels=None,
    )


@pytest.fixture
def classification_file_minimal_data():
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    workflow_params = WorkflowParamsDict(document_type_id=None)

    return FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name="minimal_classification.pdf",
        path="/uploads/minimal_classification.pdf",
        group_id=group_id,
        workflow_params=workflow_params,
        labels=None,
    )


@pytest.fixture
def processing_file_full_data(test_workflow_params):
    tenant_id = str(uuid4())
    name = "processing_test.pdf"
    path = "/uploads/processing_test.pdf"
    group_id = str(uuid4())

    return FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
    )


@pytest.fixture
def processing_file_no_group(test_workflow_params):
    tenant_id = str(uuid4())

    return FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name="processing_no_group.pdf",
        path="/uploads/processing_no_group.pdf",
        group_id=None,
        workflow_params=test_workflow_params,
    )


@pytest.fixture
def processing_file_minimal_data():
    tenant_id = str(uuid4())
    workflow_params = WorkflowParamsDict(document_type_id=None)

    return FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name="minimal_processing.pdf",
        path="/uploads/minimal_processing.pdf",
        group_id=None,
        workflow_params=workflow_params,
    )


@pytest.fixture
def factory_files_for_state_testing(test_workflow_params):
    tenant_id = str(uuid4())
    name = "state_test.pdf"
    path = "/uploads/state_test.pdf"
    group_id = str(uuid4())

    splitting_file = FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        classification_enabled=True,
        workflow_params=test_workflow_params,
        labels=None,
    )

    classification_file = FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
        labels=None,
    )

    processing_file = FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
    )

    return splitting_file, classification_file, processing_file


@pytest.fixture
def factory_files_for_id_testing(test_workflow_params):
    tenant_id = str(uuid4())
    name = "unique_id_test.pdf"
    path = "/uploads/unique_id_test.pdf"
    group_id = str(uuid4())

    file_1 = FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        classification_enabled=True,
        workflow_params=test_workflow_params,
        labels=None,
    )

    file_2 = FileFactory.create_for_classification(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
        labels=None,
    )

    file_3 = FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=group_id,
        workflow_params=test_workflow_params,
    )

    return file_1, file_2, file_3


@pytest.fixture
def factory_file_with_none_values():
    tenant_id = str(uuid4())
    name = "none_test.pdf"
    path = "/uploads/none_test.pdf"
    workflow_params = WorkflowParamsDict(document_type_id=None)

    return FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name=name,
        path=path,
        group_id=None,
        workflow_params=workflow_params,
    )


@pytest.fixture
def file_info_params(file_name, file_path, document_type_id):
    return {
        "name": file_name,
        "path": file_path,
        "document_type_id": document_type_id,
    }
