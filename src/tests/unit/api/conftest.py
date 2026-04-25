from unittest.mock import Mock

import pytest

from deps_file.domain.model import FileFactory, WorkflowParamsDict


@pytest.fixture
def command_file_service_mock(containers):
    return containers.command_file_service


@pytest.fixture
def file_service_mock(mocker, command_file_service_mock):
    mock = mocker.Mock(command_file_service_mock.cls)
    command_file_service_mock.override(mock)
    yield mock

    command_file_service_mock.reset_override()


@pytest.fixture
def seed_api_files(test_file_1_tenant_id):
    tenant_id = test_file_1_tenant_id()
    return FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name="alpha_doc.pdf",
        path="/u/a.pdf",
        group_id=None,
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
