import json
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import pytest

from deps_file.constants import BASE_API_PREFIX, DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE
from deps_file.domain.exceptions import FileNotFound
from deps_file.domain.model import (
    FileDeleted,
    FileDetailsInfo,
    FileSortBy,
    FileSortOrder,
    ReferenceType,
)

ENDPOINT = f"{BASE_API_PREFIX}/v1/files"


@pytest.mark.parametrize(
    "query",
    [
        {},
        {"name": "Doc"},
        {"state": "COMPLETED"},
        [("state", "COMPLETED"), ("state", "FAILED")],
        {"dateStart": "2024-01-01T00:00:00Z", "dateEnd": "2024-12-31T23:59:59Z"},
        [("labels", "alpha"), ("labels", "beta")],
        {"sortBy": "name", "sortOrder": "asc"},
        {"sortBy": "state", "sortOrder": "desc"},
        {"page": 2, "perPage": 5},
    ],
)
def test_list_files_calls_service_with_correct_args(client, query):
    r = client.get(ENDPOINT, params=query)
    assert r.status_code == 200


@pytest.mark.parametrize(
    "query",
    [
        {"page": 0},
        {"perPage": 0},
        {"perPage": 101},
        {"sortBy": "bad"},
        {"sortOrder": "bad"},
    ],
)
def test_list_files_validation_errors(client, query):
    r = client.get(ENDPOINT, params=query)
    assert r.status_code == 422


def test_list_files_labels_aggregated_to_list(client, mock_query_file_service_autouse):
    params = [("labels", "alpha"), ("labels", "beta")]

    r = client.get(ENDPOINT, params=params)
    assert r.status_code == 200

    svc = mock_query_file_service_autouse
    svc.find_all_with.assert_called_once()
    kwargs = svc.find_all_with.call_args.kwargs

    assert kwargs["labels"] == ["alpha", "beta"]


def test_list_files_state_aggregated_to_list(client, mock_query_file_service_autouse):
    params = [("state", "COMPLETED"), ("state", "FAILED")]

    r = client.get(ENDPOINT, params=params)
    assert r.status_code == 200

    svc = mock_query_file_service_autouse
    svc.find_all_with.assert_called_once()
    kwargs = svc.find_all_with.call_args.kwargs

    assert kwargs["state"] == ["COMPLETED", "FAILED"]


def test_list_files_defaults_for_pagination_and_sort(client, mock_query_file_service_autouse):
    r = client.get(ENDPOINT)
    assert r.status_code == 200

    svc = mock_query_file_service_autouse
    svc.find_all_with.assert_called_once()
    kwargs = svc.find_all_with.call_args.kwargs

    assert kwargs["page"] == DEFAULT_PAGE_NUMBER
    assert kwargs["per_page"] == DEFAULT_PAGE_SIZE
    assert kwargs["sort_by"] == FileSortBy.CREATED_AT
    assert kwargs["sort_order"] == FileSortOrder.DESC
    assert kwargs["name"] is None
    assert kwargs["state"] is None
    assert kwargs["labels"] is None
    assert kwargs["date_start"] is None
    assert kwargs["date_end"] is None


def test_get_file__existing_file__returns_file_response(client, tenant_id, mock_query_file_service_autouse):
    file_id = str(uuid4())

    file_details = FileDetailsInfo(
        file_id=file_id,
        tenant_id=tenant_id(),
        name="test_document.pdf",
        path="/storage/test_document.pdf",
        state={"status": "PROCESSING", "error_message": None},
        processing_params={
            "group_id": str(uuid4()),
            "splitting_enabled": False,
            "classification_enabled": True,
            "workflow_params": {
                "document_type_id": str(uuid4()),
                "engine": None,
                "language": None,
                "llm_type": None,
                "parsing_features": [],
                "needs_unifier": True,
                "needs_extraction": False,
                "assigned_to_me": True,
                "metadata": {},
            },
        },
        labels=["test", "document"],
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        updated_at=datetime(2023, 1, 1, 1, 0, 0),
    )

    mock_query_file_service_autouse.find_file.return_value = file_details

    response = client.get(f"{ENDPOINT}/{file_id}")

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == file_id
    assert response_data["tenantId"] == tenant_id()
    assert response_data["name"] == "test_document.pdf"
    assert response_data["path"] == "/storage/test_document.pdf"
    assert response_data["state"]["status"] == "PROCESSING"
    assert response_data["labels"] == ["test", "document"]

    mock_query_file_service_autouse.find_file.assert_called_once_with(file_id=file_id, tenant_id=tenant_id())


def test_get_file__non_existing_file__returns_404(client, tenant_id, mock_query_file_service_autouse):
    file_id = str(uuid4())

    mock_query_file_service_autouse.find_file.side_effect = FileNotFound(file_id)

    response = client.get(f"{ENDPOINT}/{file_id}")

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert file_id in response_data["message"]

    mock_query_file_service_autouse.find_file.assert_called_once_with(file_id=file_id, tenant_id=tenant_id())


def test_get_file__with_minimal_file_data__returns_file_response(client, tenant_id, mock_query_file_service_autouse):
    file_id = str(uuid4())

    file_details = FileDetailsInfo(
        file_id=file_id,
        tenant_id=tenant_id(),
        name="minimal.pdf",
        path="/storage/minimal.pdf",
        state={"status": "CREATED"},
        processing_params={
            "splitting_enabled": False,
            "classification_enabled": False,
            "workflow_params": {
                "needs_unifier": False,
                "needs_extraction": False,
                "assigned_to_me": False,
                "parsing_features": [],
                "metadata": {},
            },
        },
        labels=None,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        updated_at=None,
    )

    mock_query_file_service_autouse.find_file.return_value = file_details

    response = client.get(f"{ENDPOINT}/{file_id}")

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == file_id
    assert response_data["name"] == "minimal.pdf"
    assert response_data["labels"] == []
    assert response_data["updatedAt"] is None


def test_get_file__calls_service_with_correct_tenant_isolation(client, tenant_id, mock_query_file_service_autouse):
    file_id = str(uuid4())

    file_details = FileDetailsInfo(
        file_id=file_id,
        tenant_id=tenant_id(),
        name="test.pdf",
        path="/storage/test.pdf",
        state={"status": "PROCESSING"},
        processing_params={
            "splitting_enabled": False,
            "classification_enabled": False,
            "workflow_params": {
                "needs_unifier": False,
                "needs_extraction": False,
                "assigned_to_me": False,
            },
        },
        labels=None,
        created_at=datetime(2023, 1, 1, 0, 0, 0),
        updated_at=None,
    )

    mock_query_file_service_autouse.find_file.return_value = file_details

    client.get(f"{ENDPOINT}/{file_id}")

    mock_query_file_service_autouse.find_file.assert_called_once_with(file_id=file_id, tenant_id=tenant_id())


@pytest.mark.usefixtures("save_file", "save_group")
def test_classify_existing_file__valid_request__calls_service_and_returns_204(
    client, tenant_id, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "engine": "tesseract",
        "language": "eng",
        "llmType": "gpt-4",
        "parsingFeatures": ["tables", "images"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
        "metadata": {"priority": "high"},
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 204


@pytest.mark.usefixtures("save_file", "save_group")
def test_classify_existing_file__minimal_request__calls_service_and_returns_204(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 204


@pytest.mark.usefixtures("save_file", "save_group")
def test_classify_existing_file__non_existing_file__returns_404(client, command_file_service, test_group_1_id):
    file_id = str(uuid4())

    request_body = {
        "groupId": test_group_1_id(),
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert file_id in response_data["message"]


@pytest.mark.usefixtures("save_file")
def test_classify_existing_file__non_existing_group__returns_404(
    client,
    tenant_id,
    command_file_service,
    fake_unit_of_work,
    test_file_1_id,
    test_group_1_id,
):
    request_body = {
        "groupId": test_group_1_id(),
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "group_not_found"
    assert test_group_1_id() in response_data["message"]


def test_classify_existing_file__with_document_reference__returns_409(
    client, tenant_id, command_file_service, fake_unit_of_work, test_file_1, test_group_1
):
    file_id = str(test_file_1.id())
    group_id = test_group_1.id()

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Existing Document",
    )

    fake_unit_of_work.files._db[(file_id, tenant_id())] = test_file_1
    fake_unit_of_work.groups._db[(group_id, tenant_id())] = test_group_1

    request_body = {
        "groupId": group_id,
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 409
    response_data = response.json()

    assert response_data["code"] == "file_reference_already_exists"
    assert file_id in response_data["message"]


def test_classify_existing_file__with_batch_reference__returns_409(
    client, tenant_id, command_file_service, fake_unit_of_work, test_file_1, test_group_1
):
    file_id = str(test_file_1.id())
    group_id = test_group_1.id()

    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Existing Batch",
    )

    fake_unit_of_work.files._db[(file_id, tenant_id())] = test_file_1
    fake_unit_of_work.groups._db[(group_id, tenant_id())] = test_group_1

    request_body = {
        "groupId": group_id,
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 409
    response_data = response.json()

    assert response_data["code"] == "file_reference_already_exists"
    assert file_id in response_data["message"]


@pytest.mark.parametrize(
    "invalid_body",
    [
        {},
        {"groupId": "test"},
        {"groupId": "test", "needsUnifier": True},
        {"groupId": "test", "needsExtraction": False},
        {"groupId": "test", "assignedToMe": True},
        {"needsUnifier": True, "needsExtraction": False, "assignedToMe": True},
    ],
)
def test_classify_existing_file__missing_required_fields__returns_422(client, invalid_body):
    file_id = str(uuid4())

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=invalid_body)

    assert response.status_code == 422


@pytest.mark.usefixtures("save_file", "save_group")
def test_classify_existing_file__workflow_params_passed_correctly_to_service(
    client,
    tenant_id,
    command_file_service,
    test_file_1_id,
    test_group_1_id,
    mocker,
):
    spy_classify_file = mocker.spy(command_file_service, "classify_file")

    request_body = {
        "groupId": test_group_1_id(),
        "engine": "tesseract",
        "language": "eng",
        "llmType": "gpt-4",
        "parsingFeatures": ["tables", "images"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
        "metadata": {"priority": "high"},
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 204

    spy_classify_file.assert_called_once()
    call_kwargs = spy_classify_file.call_args.kwargs

    assert call_kwargs["file_id"] == test_file_1_id()
    assert call_kwargs["tenant_id"] == tenant_id()
    assert call_kwargs["group_id"] == test_group_1_id()

    workflow_params = call_kwargs["workflow_params"]
    assert workflow_params["engine"] == "tesseract"
    assert workflow_params["language"] == "eng"
    assert workflow_params["llm_type"] == "gpt-4"
    assert workflow_params["parsing_features"] == ["tables", "images"]
    assert workflow_params["needs_unifier"] is True
    assert workflow_params["needs_extraction"] is False
    assert workflow_params["assigned_to_me"] is True
    assert workflow_params["metadata"] == {"priority": "high"}


@pytest.mark.usefixtures("save_file", "save_group")
def test_classify_existing_file__parsing_features_normalized_from_comma_separated(
    client,
    command_file_service,
    test_file_1_id,
    test_group_1_id,
    mocker,
):
    spy_classify_file = mocker.spy(command_file_service, "classify_file")

    request_body = {
        "groupId": test_group_1_id(),
        "parsingFeatures": ["tables, images", "charts"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 204

    workflow_params = spy_classify_file.call_args.kwargs["workflow_params"]
    assert workflow_params["parsing_features"] == ["tables", "images", "charts"]


@pytest.mark.usefixtures("save_file")
def test_classify_existing_file__tenant_isolation_enforced(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/classify", json=request_body)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["code"] == "group_not_found"


def test_process_file_endpoint__decodes_filename(client, file_service_mock, seed_api_files):
    fake_content = b"PDF content"
    fake_filename = "Alpha%20Doc.pdf"
    expected_name = "Alpha Doc.pdf"

    file_service_mock.process.return_value = seed_api_files

    form_data = {
        "parsingFeatures": json.dumps(["feature1", "feature2"]),
        "needsUnifier": True,
        "needsExtraction": True,
        "assignedToMe": False,
        "llmType": "gpt-3",
        "engine": "some_engine",
        "language": "en",
        "metadata": json.dumps({"key": "value"}),
        "labels": json.dumps(["label1", "label2"]),
    }

    response = client.post(
        ENDPOINT + "/process",
        files={"file": (fake_filename, BytesIO(fake_content))},
        data=form_data,
    )

    assert response.status_code == 201

    file_service_mock.process.assert_called_once()
    call_kwargs = file_service_mock.process.call_args.kwargs

    assert call_kwargs["name"] == expected_name


def test_classify_file_endpoint__decodes_filename(client, file_service_mock, seed_api_files):
    fake_content = b"PDF content"
    fake_filename = "Alpha%20Doc.pdf"
    expected_name = "Alpha Doc.pdf"

    file_service_mock.classify.return_value = seed_api_files

    form_data = {
        "groupId": "test-group",
        "parsingFeatures": json.dumps(["feature1", "feature2"]),
        "needsUnifier": True,
        "needsExtraction": True,
        "assignedToMe": False,
        "llmType": "gpt-3",
        "engine": "some_engine",
        "language": "en",
        "metadata": json.dumps({"key": "value"}),
        "labels": json.dumps(["label1", "label2"]),
    }

    response = client.post(
        ENDPOINT + "/classify",
        files={"file": (fake_filename, BytesIO(fake_content))},
        data=form_data,
    )

    assert response.status_code == 201

    file_service_mock.classify.assert_called_once()
    call_kwargs = file_service_mock.classify.call_args.kwargs

    assert call_kwargs["name"] == expected_name


def test_get_file_content__existing_file__returns_content_with_headers(
    client, tenant_id, mocker, command_file_service, test_file_1_id
):
    file_name = "test_document.pdf"
    file_content = b"PDF file content here"

    mocker.patch.object(
        command_file_service,
        "get_file_content",
        return_value=(file_content, file_name),
    )

    response = client.get(f"{ENDPOINT}/{test_file_1_id()}/content")

    assert response.status_code == 200
    assert response.content == file_content
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"] == f'attachment; filename="{file_name}"'

    command_file_service.get_file_content.assert_called_once_with(file_id=test_file_1_id(), tenant_id=tenant_id())


def test_get_file_content__non_existing_file__returns_404(
    client, tenant_id, mocker, command_file_service, test_file_1_id
):
    mocker.patch.object(
        command_file_service,
        "get_file_content",
        side_effect=FileNotFound(test_file_1_id()),
    )

    response = client.get(f"{ENDPOINT}/{test_file_1_id()}/content")

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert test_file_1_id() in response_data["message"]

    command_file_service.get_file_content.assert_called_once_with(file_id=test_file_1_id(), tenant_id=tenant_id())


def test_get_file_content__with_special_characters_in_filename__returns_content_with_proper_headers(
    client, tenant_id, mocker, command_file_service, test_file_1_id
):
    file_name = 'test "document" (2024).pdf'
    file_content = b"Test content"

    mocker.patch.object(
        command_file_service,
        "get_file_content",
        return_value=(file_content, file_name),
    )

    response = client.get(f"{ENDPOINT}/{test_file_1_id()}/content")

    assert response.status_code == 200
    assert response.content == file_content
    assert response.headers["content-disposition"] == f'attachment; filename="{file_name}"'


def test_get_file_content__with_large_file__returns_full_content(client, mocker, command_file_service, test_file_1_id):
    file_name = "large_file.pdf"
    file_content = b"x" * (10 * 1024 * 1024)

    mocker.patch.object(
        command_file_service,
        "get_file_content",
        return_value=(file_content, file_name),
    )

    response = client.get(f"{ENDPOINT}/{test_file_1_id()}/content")

    assert response.status_code == 200
    assert len(response.content) == 10 * 1024 * 1024
    assert response.content == file_content


def test_splitting_file_endpoint__decodes_filename(client, file_service_mock, seed_api_files):
    fake_content = b"PDF content"
    fake_filename = "Alpha%20Doc.pdf"
    expected_name = "Alpha Doc.pdf"

    file_service_mock.split.return_value = seed_api_files

    form_data = {
        "groupId": "test-group",
        "classificationEnabled": True,
        "parsingFeatures": json.dumps(["feature1", "feature2"]),
        "needsUnifier": True,
        "needsExtraction": True,
        "assignedToMe": False,
        "llmType": "gpt-3",
        "engine": "some_engine",
        "language": "en",
        "metadata": json.dumps({"key": "value"}),
        "labels": json.dumps(["label1", "label2"]),
    }

    response = client.post(
        ENDPOINT + "/split",
        files={"file": (fake_filename, BytesIO(fake_content))},
        data=form_data,
    )

    assert response.status_code == 201

    file_service_mock.split.assert_called_once()
    call_kwargs = file_service_mock.split.call_args.kwargs

    assert call_kwargs["name"] == expected_name


@pytest.mark.usefixtures("save_file", "save_group")
def test_splitting_existing_file__valid_request__calls_service_and_returns_204(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "engine": "tesseract",
        "language": "eng",
        "llmType": "gpt-4",
        "parsingFeatures": ["tables", "images"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
        "metadata": {"priority": "high"},
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 204


@pytest.mark.usefixtures("save_file", "save_group")
def test_splitting_existing_file__minimal_request__calls_service_and_returns_204(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 204


@pytest.mark.usefixtures("save_group")
def test_splitting_existing_file__non_existing_file__returns_404(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": False,
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert test_file_1_id() in response_data["message"]


@pytest.mark.usefixtures("save_file")
def test_splitting_existing_file__non_existing_group__returns_404(
    client, tenant_id, command_file_service, fake_unit_of_work, test_file_1, test_file_1_id, test_group_1_id
):
    fake_unit_of_work.files._db[(test_file_1_id(), tenant_id())] = test_file_1

    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "group_not_found"
    assert test_group_1_id() in response_data["message"]


@pytest.mark.parametrize(
    "invalid_body",
    [
        {},
        {"groupId": "test"},
        {"groupId": "test", "needsUnifier": True},
        {"groupId": "test", "needsExtraction": False},
        {"groupId": "test", "assignedToMe": True},
        {"needsUnifier": True, "needsExtraction": False, "assignedToMe": True},
    ],
)
def test_splitting_existing_file__missing_required_fields__returns_422(client, invalid_body):
    file_id = str(uuid4())

    response = client.patch(f"{ENDPOINT}/{file_id}/split", json=invalid_body)

    assert response.status_code == 422


@pytest.mark.usefixtures("save_file", "save_group")
def test_splitting_existing_file__workflow_params_passed_correctly_to_service(
    client,
    tenant_id,
    command_file_service,
    test_file_and_group_setup,
    mocker,
    test_file_1_id,
    test_group_1_id,
):
    spy_split_file = mocker.spy(command_file_service, "split_file")

    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "engine": "tesseract",
        "language": "eng",
        "llmType": "gpt-4",
        "parsingFeatures": ["tables", "images"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
        "metadata": {"priority": "high"},
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 204

    spy_split_file.assert_called_once()
    call_kwargs = spy_split_file.call_args.kwargs

    assert call_kwargs["file_id"] == test_file_1_id()
    assert call_kwargs["tenant_id"] == tenant_id()
    assert call_kwargs["group_id"] == test_group_1_id()

    workflow_params = call_kwargs["workflow_params"]
    assert workflow_params["engine"] == "tesseract"
    assert workflow_params["language"] == "eng"
    assert workflow_params["llm_type"] == "gpt-4"
    assert workflow_params["parsing_features"] == ["tables", "images"]
    assert workflow_params["needs_unifier"] is True
    assert workflow_params["needs_extraction"] is False
    assert workflow_params["assigned_to_me"] is True
    assert workflow_params["metadata"] == {"priority": "high"}


@pytest.mark.usefixtures("save_file", "save_group")
def test_splitting_existing_file__parsing_features_normalized_from_comma_separated(
    client,
    command_file_service,
    test_file_and_group_setup,
    mocker,
    test_file_1_id,
    test_group_1_id,
):
    spy_split_file = mocker.spy(command_file_service, "split_file")

    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "parsingFeatures": ["tables, images", "charts"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 204

    workflow_params = spy_split_file.call_args.kwargs["workflow_params"]
    assert workflow_params["parsing_features"] == ["tables", "images", "charts"]


@pytest.mark.usefixtures("save_file")
def test_splitting_existing_file__tenant_isolation_enforced(
    client, command_file_service, test_file_1_id, test_group_1_id
):
    request_body = {
        "groupId": test_group_1_id(),
        "classificationEnabled": True,
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{test_file_1_id()}/split", json=request_body)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["code"] == "group_not_found"


def test_create_document_from_file__valid_request__calls_service_and_returns_201(
    client,
    tenant_id,
    command_file_service,
    mocker,
    test_file_1_id,
    document_id,
    document_type_id,
    document_name,
):
    mocker.patch.object(
        command_file_service,
        "create_document_from_file",
        return_value=(document_id, document_name),
    )

    request_body = {"documentTypeId": document_type_id}

    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/create-document", json=request_body)

    assert response.status_code == 201
    response_data = response.json()

    assert response_data["documentId"] == document_id
    assert response_data["documentName"] == document_name

    command_file_service.create_document_from_file.assert_called_once_with(
        file_id=test_file_1_id(),
        tenant_id=tenant_id(),
        document_type_id=document_type_id,
    )


def test_create_document_from_file__missing_document_type_id__returns_422(client):
    file_id = str(uuid4())

    response = client.post(f"{ENDPOINT}/{file_id}/create-document", json={})

    assert response.status_code == 422


def test_create_document_from_file__non_existing_file__returns_404(
    client,
    command_file_service,
    mocker,
    test_file_1_id,
    document_type_id,
):
    mocker.patch.object(
        command_file_service,
        "create_document_from_file",
        side_effect=FileNotFound(test_file_1_id()),
    )

    request_body = {"documentTypeId": document_type_id}

    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/create-document", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert test_file_1_id() in response_data["message"]


def test_create_batch_from_file__valid_request__calls_service_and_returns_201(
    client,
    test_group_1_id,
    tenant_id,
    command_file_service,
    mocker,
    test_file_1_id,
    batch_name,
):
    mocker.patch.object(
        command_file_service,
        "create_batch_from_file",
        return_value="batch-id-123",
    )

    request_body = {
        "batchName": batch_name,
        "groupId": test_group_1_id(),
        "files": [
            {
                "name": "file1.pdf",
                "path": "/file1.pdf",
                "documentTypeId": None,
            },
        ],
    }

    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/create-batch", json=request_body)

    assert response.status_code == 201
    response_data = response.json()

    assert response_data["batchId"] == "batch-id-123"

    expected_response_body = [
        {
            "name": "file1.pdf",
            "path": "/file1.pdf",
            "document_type_id": None,
        }
    ]

    command_file_service.create_batch_from_file.assert_called_once_with(
        file_id=test_file_1_id(),
        tenant_id=tenant_id(),
        batch_name=batch_name,
        batch_files=expected_response_body,
        group_id=test_group_1_id(),
    )


def test_create_batch_from_file__missing_required_fields__returns_422(client):
    file_id = str(uuid4())

    response = client.post(f"{ENDPOINT}/{file_id}/create-batch", json={})

    assert response.status_code == 422


def test_create_batch_from_file__non_existing_file__returns_404(client, test_file_1_id, document_type_id):
    request_body = {
        "batchName": "Test Batch",
        "groupId": None,
        "files": [
            {
                "name": "file1.pdf",
                "path": "/file1.pdf",
                "documentTypeId": document_type_id,
            },
        ],
    }

    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/create-batch", json=request_body)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert test_file_1_id() in response_data["message"]


def test_create_batch_from_file__no_group_id_and_no_document_type_id__422(client, test_file_1_id):
    request_body = {
        "batchName": "Test Batch",
        "groupId": None,
        "files": [
            {
                "name": "file1.pdf",
                "path": "/file1.pdf",
                "documentTypeId": None,
            },
        ],
    }

    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/create-batch", json=request_body)

    assert response.status_code == 422


@pytest.mark.usefixtures("save_file", "save_group")
def test_restart_file_endpoint__file_is_not_failed__returns_400(client, command_file_service, test_file_1_id):
    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/restart")

    assert response.status_code == 400


@pytest.mark.usefixtures("save_test_failed_file_for_processing", "save_group")
def test_restart_file_endpoint__file_is_failed__returns_204(client, command_file_service, test_file_for_processing):
    response = client.post(f"{ENDPOINT}/{test_file_for_processing.id()}/restart")

    assert response.status_code == 204


@pytest.mark.usefixtures("save_group")
def test_restart_file_endpoint__file_not_found__returns_404(client, test_file_1_id):
    response = client.post(f"{ENDPOINT}/{test_file_1_id()}/restart")

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert test_file_1_id() in response_data["message"]


@pytest.mark.usefixtures("save_file")
def test_delete__returns_204(
    client,
    test_file_1_id,
    file_path,
    fake_command_file_repository,
    tenant_id,
    fake_domain_event_publisher,
):
    params = {"ids": test_file_1_id()}

    response = client.delete(ENDPOINT, params=params)

    assert response.status_code == 204
    assert not fake_command_file_repository.file_of_id(id_=test_file_1_id(), tenant_id=tenant_id())
    [event] = fake_domain_event_publisher.last_published.events
    assert isinstance(event, FileDeleted)
    assert event.id == test_file_1_id()
    assert event.path == file_path
