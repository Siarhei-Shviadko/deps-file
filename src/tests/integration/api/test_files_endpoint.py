import json
from uuid import uuid4

import pytest

from deps_file.constants import BASE_API_PREFIX
from deps_file.domain.model import (
    FileFactory,
    GroupFactory,
    ReferenceType,
    WorkflowParamsDict,
)

ENDPOINT = f"{BASE_API_PREFIX}/v1/files"


@pytest.fixture
def seed_api_files_with_labels(
    unit_of_work,
    test_file_1_tenant_id,
    add_labels,
):
    tenant_id = test_file_1_tenant_id()
    f1 = FileFactory.create_for_processing(
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
    f2 = FileFactory.create_for_processing(
        tenant_id=tenant_id,
        name="beta_doc.pdf",
        path="/u/b.pdf",
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
    with unit_of_work:
        unit_of_work.files.save(f1)
        unit_of_work.files.save(f2)
        unit_of_work.commit()
    add_labels(f1.id(), ["alpha"])
    add_labels(f2.id(), ["beta", "gamma"])
    return tenant_id, f1, f2


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"name": "doc"},
        {"state": "PROCESSING"},
        [("labels", "alpha")],
        [("labels", "alpha"), ("labels", "beta")],
        {"sortBy": "name", "sortOrder": "asc"},
        {"page": 1, "perPage": 1},
    ],
)
def test_files_list_e2e(
    client,
    deps_token_headers_factory,
    seed_api_files_with_labels,
    params,
):
    tenant_id, _, _ = seed_api_files_with_labels
    headers = deps_token_headers_factory(tenant_id)
    r = client.get(ENDPOINT, params=params, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "meta" in body and "result" in body
    assert body["meta"]["size"] == len(body["result"])


def test_process_file_endpoint__file_save__file_id_returned(
    test_blob_file, client, seed_api_files_with_labels, deps_token_headers_factory
):
    file, filename = test_blob_file

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
    tenant_id, _, _ = seed_api_files_with_labels
    headers = deps_token_headers_factory(tenant_id)
    response = client.post(
        ENDPOINT + "/process",
        files={"file": (filename, file)},
        data=form_data,
        headers=headers,
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "id" in response_data
    assert isinstance(response_data["id"], str)


def test_classify_file__with_valid_request__creates_file_and_returns_201(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_group_1,
    add_single_group,
    classify_test_values,
):
    add_single_group(test_group_1)

    tenant_id = str(test_group_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    request_data = {
        "groupId": str(test_group_1.id()),
        "labels": json.dumps(classify_test_values["labels"]),
        "engine": "advanced",
        "language": "en",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/classify",
        headers=headers,
        files={"file": (classify_test_values["file_name"], classify_test_values["content"], "application/pdf")},
        data=request_data,
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "id" in response_data

    with unit_of_work:
        file = unit_of_work.files.file_of_id(response_data["id"], tenant_id)
        assert file is not None
        assert file.name == classify_test_values["file_name"]
        assert file.processing_params.classification_enabled is True
        assert file.processing_params.splitting_enabled is False
        assert file.processing_params.group_id() == str(test_group_1.id())


def test_classify_file__with_invalid_group__returns_404(
    client,
    deps_token_headers_default,
    classify_test_values,
):
    request_data = {
        "groupId": "non-existent-group-id",
        "labels": json.dumps(["test"]),
        "engine": "basic",
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/classify",
        headers=deps_token_headers_default,
        files={"file": ("test.pdf", classify_test_values["content"], "application/pdf")},
        data=request_data,
    )

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["code"] == "group_not_found"


def test_classify_file__missing_required_fields__returns_422(
    client,
    deps_token_headers_default,
    classify_test_values,
):
    form_data = {"labels": json.dumps(["test"])}

    response = client.post(
        f"{ENDPOINT}/classify",
        headers=deps_token_headers_default,
        files={"file": ("test.pdf", classify_test_values["content"], "application/pdf")},
        data=form_data,
    )

    assert response.status_code == 422


def test_classify_file__with_cross_tenant_group__returns_404(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_group_2,
    add_single_group,
    classify_test_values,
):
    add_single_group(test_group_2)

    headers = deps_token_headers_factory("tenant-1")

    request_data = {
        "groupId": str(test_group_2.id()),
        "labels": json.dumps(["test"]),
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/classify",
        headers=headers,
        files={"file": ("test.pdf", classify_test_values["content"], "application/pdf")},
        data=request_data,
    )

    assert response.status_code == 404


def test_split_file__with_valid_request__creates_file_and_returns_201(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_group_1,
    add_single_group,
    splitting_test_values,
):
    add_single_group(test_group_1)

    tenant_id = str(test_group_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    form_data = {
        "groupId": str(test_group_1.id()),
        "classificationEnabled": True,
        "labels": json.dumps(splitting_test_values["labels"]),
        "engine": "advanced",
        "language": "en",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/split",
        headers=headers,
        files={"file": (splitting_test_values["file_name"], splitting_test_values["content"], "application/pdf")},
        data=form_data,
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "id" in response_data

    with unit_of_work:
        file = unit_of_work.files.file_of_id(response_data["id"], tenant_id)
        assert file is not None
        assert file.name == splitting_test_values["file_name"]
        assert file.processing_params.classification_enabled is True
        assert file.processing_params.splitting_enabled is True
        assert file.processing_params.group_id() == str(test_group_1.id())


def test_split_file__with_invalid_group__returns_404(
    client,
    deps_token_headers_default,
    splitting_test_values,
):
    form_data = {
        "groupId": "non-existent-group-id",
        "classificationEnabled": False,
        "labels": json.dumps(["test"]),
        "engine": "basic",
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/split",
        headers=deps_token_headers_default,
        files={"file": ("test.pdf", splitting_test_values["content"], "application/pdf")},
        data=form_data,
    )

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["code"] == "group_not_found"


def test_split_file__missing_required_fields__returns_422(
    client,
    deps_token_headers_default,
    splitting_test_values,
):
    response = client.post(
        f"{ENDPOINT}/split",
        headers=deps_token_headers_default,
        files={"file": ("test.pdf", splitting_test_values["content"], "application/pdf")},
        data={"request": "invalid json"},
    )

    assert response.status_code == 422


def test_split_file__with_cross_tenant_group__returns_404(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_group_2,
    add_single_group,
    splitting_test_values,
):
    add_single_group(test_group_2)

    headers = deps_token_headers_factory("tenant-1")

    form_data = {
        "groupId": str(test_group_2.id()),
        "classificationEnabled": False,
        "labels": json.dumps(["test"]),
        "needsUnifier": False,
        "needsExtraction": False,
        "assignedToMe": False,
    }

    response = client.post(
        f"{ENDPOINT}/split",
        headers=headers,
        files={"file": ("test.pdf", splitting_test_values["content"], "application/pdf")},
        data=form_data,
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"perPage": 0},
        {"perPage": 101},
        {"sortBy": "bad"},
        {"sortOrder": "bad"},
    ],
)
def test_files_list_validation_errors_integration(
    client,
    deps_token_headers_default,
    params,
):
    r = client.get(ENDPOINT, params=params, headers=deps_token_headers_default)
    assert r.status_code == 422


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"name": "Doc"},
        {"state": "COMPLETED"},
        {"dateStart": "2024-01-01T00:00:00Z", "dateEnd": "2024-12-31T23:59:59Z"},
        [("labels", "alpha"), ("labels", "beta")],
        {"sortBy": "name", "sortOrder": "asc"},
        {"sortBy": "state", "sortOrder": "desc"},
        {"page": 2, "perPage": 5},
    ],
)
def test_files_list_different_parameters_integration(
    client,
    deps_token_headers_default,
    params,
):
    r = client.get(ENDPOINT, params=params, headers=deps_token_headers_default)
    assert r.status_code == 200
    body = r.json()
    assert "meta" in body and "result" in body


def test_delete_files__with_valid_ids__returns_204_and_deletes_files(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
    test_file_2,
):
    tenant_id = str(test_file_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.files.save(test_file_2)
        unit_of_work.commit()

    file_ids = [str(test_file_1.id()), str(test_file_2.id())]
    response = client.delete(ENDPOINT, params={"ids": file_ids}, headers=headers)

    assert response.status_code == 204
    assert response.text == ""

    with unit_of_work:
        assert unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_id) is None
        assert unit_of_work.files.file_of_id(str(test_file_2.id()), tenant_id) is None


def test_delete_files__with_single_file__returns_204_and_deletes_file(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
):
    tenant_id = str(test_file_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    response = client.delete(ENDPOINT, params={"ids": [str(test_file_1.id())]}, headers=headers)

    assert response.status_code == 204
    assert response.text == ""

    with unit_of_work:
        assert unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_id) is None


def test_delete_files__with_non_existent_ids__returns_204(
    client,
    deps_token_headers_default,
):
    non_existent_ids = ["non-existent-id-1", "non-existent-id-2"]
    response = client.delete(ENDPOINT, params={"ids": non_existent_ids}, headers=deps_token_headers_default)

    assert response.status_code == 204
    assert response.text == ""


def test_delete_files__with_empty_ids__returns_422_validation_error(
    client,
    deps_token_headers_default,
):
    response = client.delete(ENDPOINT, params={"ids": []}, headers=deps_token_headers_default)

    assert response.status_code == 422


def test_delete_files__without_ids_parameter__returns_422_validation_error(
    client,
    deps_token_headers_default,
):
    response = client.delete(ENDPOINT, headers=deps_token_headers_default)

    assert response.status_code == 422


def test_delete_files__with_mixed_existing_and_non_existent_ids__deletes_existing_files(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
    test_file_2,
):
    tenant_id = str(test_file_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.files.save(test_file_2)
        unit_of_work.commit()

    mixed_ids = [str(test_file_1.id()), "non-existent-id", str(test_file_2.id())]
    response = client.delete(ENDPOINT, params={"ids": mixed_ids}, headers=headers)

    assert response.status_code == 204
    assert response.text == ""

    with unit_of_work:
        assert unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_id) is None
        assert unit_of_work.files.file_of_id(str(test_file_2.id()), tenant_id) is None


def test_delete_files__cross_tenant_isolation__only_deletes_own_tenant_files(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
    test_file_2,
):
    tenant_1_id = str(test_file_1.tenant_id())
    tenant_2_id = str(test_file_2.tenant_id())
    headers_tenant_1 = deps_token_headers_factory(tenant_1_id)

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.files.save(test_file_2)
        unit_of_work.commit()

    file_ids = [str(test_file_1.id()), str(test_file_2.id())]
    response = client.delete(ENDPOINT, params={"ids": file_ids}, headers=headers_tenant_1)

    assert response.status_code == 204

    with unit_of_work:
        assert unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_1_id) is None
        assert unit_of_work.files.file_of_id(str(test_file_2.id()), tenant_2_id) is not None


@pytest.mark.parametrize(
    "invalid_ids",
    [
        [""],
        ["   "],
        [None],
    ],
)
def test_delete_files__with_invalid_id_formats__handles_gracefully(
    client,
    deps_token_headers_default,
    invalid_ids,
):
    response = client.delete(ENDPOINT, params={"ids": invalid_ids}, headers=deps_token_headers_default)

    assert response.status_code in [204, 422]


def test_delete_files__with_duplicate_ids__handles_gracefully(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
):
    tenant_id = str(test_file_1.tenant_id())
    headers = deps_token_headers_factory(tenant_id)

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    file_id = str(test_file_1.id())
    duplicate_ids = [file_id, file_id, file_id]
    response = client.delete(ENDPOINT, params={"ids": duplicate_ids}, headers=headers)

    assert response.status_code == 204

    with unit_of_work:
        assert unit_of_work.files.file_of_id(file_id, tenant_id) is None


def test_delete_files__with_large_number_of_ids__handles_efficiently(
    client,
    deps_token_headers_default,
):
    many_ids = [f"id-{i}" for i in range(100)]
    response = client.delete(ENDPOINT, params={"ids": many_ids}, headers=deps_token_headers_default)

    assert response.status_code == 204


def test_get_file__existing_file__returns_file_details_integration(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
    add_single_file,
):
    tenant_id = test_file_1.tenant_id()
    add_single_file(test_file_1)
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{test_file_1.id()}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == test_file_1.id()
    assert response_data["tenantId"] == tenant_id
    assert response_data["name"] == test_file_1.name
    assert response_data["path"] == test_file_1.path
    assert response_data["state"]["status"] == test_file_1.state.status.value
    assert "createdAt" in response_data
    assert "processingParams" in response_data


def test_get_file__non_existing_file__returns_404_integration(
    client,
    deps_token_headers_factory,
):
    non_existing_id = str(uuid4())
    tenant_id = "test_tenant"
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{non_existing_id}", headers=headers)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert non_existing_id in response_data["message"]


def test_get_file__with_labels__returns_file_with_labels_integration(
    client,
    deps_token_headers_factory,
    unit_of_work,
    test_file_1,
    add_single_file,
    add_labels,
):
    tenant_id = test_file_1.tenant_id()
    add_single_file(test_file_1)
    add_labels(test_file_1.id(), ["integration", "test", "labels"])
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{test_file_1.id()}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()

    expected_labels = ["test_label", "integration", "test", "labels"]
    assert sorted(response_data["labels"]) == sorted(expected_labels)


def test_get_file__with_complete_processing_params__returns_full_data_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
):
    tenant_id = test_file_1.tenant_id()
    add_single_file(test_file_1)
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{test_file_1.id()}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()

    assert "processingParams" in response_data
    assert "workflowParams" in response_data["processingParams"]
    assert (
        response_data["processingParams"]["classificationEnabled"]
        == test_file_1.processing_params.classification_enabled
    )
    assert response_data["processingParams"]["splittingEnabled"] == test_file_1.processing_params.splitting_enabled


def test_get_file__without_reference__returns_file_with_null_reference_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
):
    add_single_file(test_file_1)
    tenant_id = test_file_1.tenant_id()
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{test_file_1.id()}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()

    assert "reference" in response_data
    assert response_data["reference"] is None


def test_get_file__with_reference__returns_file_with_reference_data_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
):
    entity_id = str(uuid4())
    entity_name = "Test Document 1"

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )
    add_single_file(test_file_1)

    tenant_id = test_file_1.tenant_id()
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{test_file_1.id()}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()

    assert "reference" in response_data
    assert response_data["reference"] is not None
    assert response_data["reference"]["entityType"] == ReferenceType.DOCUMENT.value
    assert response_data["reference"]["entityId"] == entity_id
    assert response_data["reference"]["entityName"] == entity_name


def test_list_files__with_reference_available_true__returns_only_files_with_references(
    client,
    tenant_id,
    unit_of_work,
    test_file_1_tenant_id,
):
    file_with_ref = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="file_with_ref.pdf",
        path="/u/ref.pdf",
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
    file_with_ref._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Test Document",
    )

    file_without_ref = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="file_without_ref.pdf",
        path="/u/noref.pdf",
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

    with unit_of_work:
        unit_of_work.files.save(file_with_ref)
        unit_of_work.files.save(file_without_ref)
        unit_of_work.commit()

    response = client.get(ENDPOINT, params={"referenceAvailable": "true"})

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["meta"]["size"] == 1
    assert len(response_data["result"]) == 1
    assert response_data["result"][0]["id"] == str(file_with_ref.id())
    assert response_data["result"][0]["reference"] is not None


def test_list_files__with_reference_available_false__returns_all_files(
    client,
    tenant_id,
    unit_of_work,
    test_file_1_tenant_id,
):
    file_with_ref = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="file_with_ref.pdf",
        path="/u/ref.pdf",
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
    file_with_ref._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Test Document",
    )

    file_without_ref = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="file_without_ref.pdf",
        path="/u/noref.pdf",
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

    with unit_of_work:
        unit_of_work.files.save(file_with_ref)
        unit_of_work.files.save(file_without_ref)
        unit_of_work.commit()

    response_false = client.get(ENDPOINT, params={"referenceAvailable": "false"})
    assert response_false.status_code == 200
    data_false = response_false.json()
    assert data_false["meta"]["size"] == 2

    response_no_param = client.get(ENDPOINT)
    assert response_no_param.status_code == 200
    data_no_param = response_no_param.json()
    assert data_no_param["meta"]["size"] == 2


def test_list_files__with_reference_filter__returns_matching_files(
    client,
    tenant_id,
    unit_of_work,
    test_file_1_tenant_id,
):
    invoice_file = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="invoice.pdf",
        path="/u/invoice.pdf",
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
    invoice_file._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Medical Invoice",
    )

    passport_file = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name="passport.pdf",
        path="/u/passport.pdf",
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
    passport_file._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Passport Document",
    )

    with unit_of_work:
        unit_of_work.files.save(invoice_file)
        unit_of_work.files.save(passport_file)
        unit_of_work.commit()

    response = client.get(ENDPOINT, params={"reference": "Invoice"})

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["meta"]["size"] == 1
    assert len(response_data["result"]) == 1
    assert response_data["result"][0]["id"] == str(invoice_file.id())
    assert response_data["result"][0]["reference"]["entityName"] == "Medical Invoice"


def test_classify_existing_file__with_valid_request__returns_204_integration(
    client,
    unit_of_work,
    tenant_id,
    add_single_file,
    test_file_1,
    add_single_group,
):
    file_id = str(test_file_1.id())
    group_id = str(uuid4())

    test_group = GroupFactory.create(id_=group_id, tenant_id=tenant_id(), is_deleted=False)

    add_single_file(test_file_1)
    add_single_group(test_group)

    request_body = {
        "groupId": group_id,
        "engine": "tesseract",
        "language": "eng",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 204

    with unit_of_work:
        file = unit_of_work.files.file_of_id(file_id, tenant_id())
        assert file is not None


def test_classify_existing_file__with_document_reference__returns_409_integration(
    client,
    unit_of_work,
    test_file_1_tenant_id,
    tenant_id,
    add_single_file,
    test_file_1,
    add_single_group,
):
    file_id = str(test_file_1.id())
    group_id = str(uuid4())

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Existing Document",
    )

    test_group = GroupFactory.create(id_=group_id, tenant_id=tenant_id(), is_deleted=False)

    add_single_file(test_file_1)
    add_single_group(test_group)

    request_body = {
        "groupId": group_id,
        "engine": "tesseract",
        "language": "eng",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 409
    response_data = response.json()

    assert response_data["code"] == "file_reference_already_exists"
    assert file_id in response_data["message"]


def test_classify_existing_file__with_batch_reference__returns_409_integration(
    client,
    unit_of_work,
    tenant_id,
    add_single_file,
    test_file_1,
    add_single_group,
):
    file_id = str(test_file_1.id())
    group_id = str(uuid4())

    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Existing Batch",
    )

    test_group = GroupFactory.create(id_=group_id, tenant_id=tenant_id(), is_deleted=False)

    add_single_file(test_file_1)
    add_single_group(test_group)

    request_body = {
        "groupId": group_id,
        "engine": "tesseract",
        "language": "eng",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/classify", json=request_body)

    assert response.status_code == 409
    response_data = response.json()

    assert response_data["code"] == "file_reference_already_exists"
    assert file_id in response_data["message"]


def test_splitting_existing_file__with_valid_request__returns_204_integration(
    client,
    unit_of_work,
    tenant_id,
    add_single_file,
    test_file_1,
    add_single_group,
):
    file_id = str(test_file_1.id())
    group_id = str(uuid4())

    test_group = GroupFactory.create(id_=group_id, tenant_id=tenant_id(), is_deleted=False)

    add_single_file(test_file_1)
    add_single_group(test_group)

    request_body = {
        "groupId": group_id,
        "classificationEnabled": True,
        "engine": "tesseract",
        "language": "eng",
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    response = client.patch(f"{ENDPOINT}/{file_id}/split", json=request_body)

    assert response.status_code == 204

    with unit_of_work:
        file = unit_of_work.files.file_of_id(file_id, tenant_id())
        assert file is not None


def test_get_file_content__existing_file__returns_content_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
    command_file_service,
):
    tenant_id = test_file_1.tenant_id()
    file_id = str(test_file_1.id())
    file_content = b"Test PDF content for integration test"

    command_file_service._object_storage._storage[test_file_1.path] = file_content
    add_single_file(test_file_1)

    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{file_id}/content", headers=headers)

    assert response.status_code == 200
    assert response.content == file_content
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"] == f'attachment; filename="{test_file_1.name}"'


def test_get_file_content__non_existing_file__returns_404_integration(
    client,
    deps_token_headers_factory,
):
    non_existing_id = str(uuid4())
    tenant_id = "test_tenant"
    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{non_existing_id}/content", headers=headers)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["code"] == "file_not_found"
    assert non_existing_id in response_data["message"]


def test_get_file_content__with_binary_content__returns_exact_bytes_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
    command_file_service,
):
    tenant_id = test_file_1.tenant_id()
    file_id = str(test_file_1.id())
    binary_content = bytes([0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34])

    command_file_service._object_storage._storage[test_file_1.path] = binary_content
    add_single_file(test_file_1)

    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{file_id}/content", headers=headers)

    assert response.status_code == 200
    assert response.content == binary_content
    assert len(response.content) == 8


def test_get_file_content__with_empty_file__returns_empty_content_integration(
    client,
    deps_token_headers_factory,
    test_file_1,
    add_single_file,
    command_file_service,
):
    tenant_id = test_file_1.tenant_id()
    file_id = str(test_file_1.id())
    empty_content = b""

    command_file_service._object_storage._storage[test_file_1.path] = empty_content
    add_single_file(test_file_1)

    headers = deps_token_headers_factory(tenant_id=tenant_id)

    response = client.get(f"{ENDPOINT}/{file_id}/content", headers=headers)

    assert response.status_code == 200
    assert response.content == empty_content
    assert len(response.content) == 0
