from uuid import uuid4

import pytest

from deps_file.domain.exceptions import FileNotFound
from tests.shared_fixtures.file import *


def test_find_file__existing_file__returns_file_details(test_file_1, query_file_service, query_file_repository):
    query_file_repository._db[(test_file_1.id(), test_file_1.tenant_id())] = test_file_1

    result = query_file_service.find_file(file_id=test_file_1.id(), tenant_id=test_file_1.tenant_id())

    assert "file_id" in result
    assert "tenant_id" in result
    assert "name" in result
    assert "path" in result
    assert result["file_id"] == test_file_1.id()
    assert result["tenant_id"] == test_file_1.tenant_id()
    assert result["name"] == test_file_1.name
    assert result["path"] == test_file_1.path


def test_find_file__non_existing_file__raises_file_not_found(query_file_service):
    file_id = str(uuid4())
    tenant_id = str(uuid4())

    with pytest.raises(FileNotFound) as exc_info:
        query_file_service.find_file(file_id=file_id, tenant_id=tenant_id)

    assert exc_info.value.code == "file_not_found"


def test_find_file__wrong_tenant__raises_file_not_found(test_file_1, query_file_service, query_file_repository):
    query_file_repository._db[(test_file_1.id(), test_file_1.tenant_id())] = test_file_1

    wrong_tenant_id = str(uuid4())

    with pytest.raises(FileNotFound) as exc_info:
        query_file_service.find_file(file_id=test_file_1.id(), tenant_id=wrong_tenant_id)

    assert exc_info.value.code == "file_not_found"


def test_find_file__calls_repository_with_correct_parameters(query_file_service, query_file_repository, mocker):
    mock_find_file = mocker.patch.object(query_file_repository, "find_file")
    mock_find_file.return_value = {
        "file_id": "test_id",
        "tenant_id": "test_tenant",
        "name": "test.pdf",
        "path": "/test.pdf",
        "state": {"status": "PROCESSING"},
        "processing_params": {
            "splitting_enabled": False,
            "classification_enabled": False,
            "workflow_params": {
                "needs_unifier": False,
                "needs_extraction": False,
                "assigned_to_me": False,
            },
        },
        "labels": None,
        "created_at": None,
        "updated_at": None,
    }

    file_id = str(uuid4())
    tenant_id = str(uuid4())

    query_file_service.find_file(file_id=file_id, tenant_id=tenant_id)

    mock_find_file.assert_called_once_with(file_id=file_id, tenant_id=tenant_id)
