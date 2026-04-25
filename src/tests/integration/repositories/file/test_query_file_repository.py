from uuid import uuid4

from deps_file.domain.model import ReferenceType


def test_file_of_id(test_file_1, query_file_repository, add_single_file):
    add_single_file(test_file_1)

    found_file = query_file_repository.file_of_id(
        file_id=test_file_1.id(),
        tenant_id=test_file_1.tenant_id(),
    )

    assert found_file is not None
    assert found_file["file_id"] == test_file_1.id()
    assert found_file["tenant_id"] == test_file_1.tenant_id()
    assert found_file["name"] == test_file_1.name
    assert found_file["path"] == test_file_1.path
    assert found_file["state"]["status"] == test_file_1.state.status.value


def test_file_of_id__not_found(
    query_file_repository,
    test_file_1_tenant_id,
    add_files,
):
    result = query_file_repository.file_of_id(
        file_id=uuid4().hex,
        tenant_id=test_file_1_tenant_id(),
    )

    assert result is None


def test_file_of_id__wrong_tenant(
    test_file_1,
    test_file_2_tenant_id,
    query_file_repository,
    add_single_file,
):
    add_single_file(test_file_1)

    result = query_file_repository.file_of_id(
        file_id=test_file_1.id(),
        tenant_id=test_file_2_tenant_id(),
    )

    assert result is None


def test_file_of_id__with_complete_data(
    integration_file_with_complete_data,
    query_file_repository,
    add_single_file,
):
    file = integration_file_with_complete_data
    add_single_file(file)

    found_file = query_file_repository.file_of_id(
        file_id=file.id(),
        tenant_id=file.tenant_id(),
    )

    assert found_file is not None
    expected_group_id = getattr(file.processing_params.group_id, "value", file.processing_params.group_id)
    assert found_file["processing_params"].get("group_id") == expected_group_id
    assert found_file["processing_params"].get("splitting_enabled") == file.processing_params.splitting_enabled
    assert (
        found_file["processing_params"].get("classification_enabled") == file.processing_params.classification_enabled
    )
    assert found_file["created_at"] is not None
    assert found_file["updated_at"] is not None


def test_file_of_id__with_minimal_data(
    integration_file_with_minimal_data,
    query_file_repository,
    add_single_file,
):
    file = integration_file_with_minimal_data
    add_single_file(file)

    found_file = query_file_repository.file_of_id(
        file_id=file.id(),
        tenant_id=file.tenant_id(),
    )

    assert found_file is not None
    assert found_file["processing_params"]["group_id"] is None
    assert found_file["processing_params"]["splitting_enabled"] is False
    assert found_file["processing_params"]["classification_enabled"] is False


def test_file_of_id__with_reference__returns_reference_data(
    test_file_1,
    query_file_repository,
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

    found_file = query_file_repository.file_of_id(
        file_id=test_file_1.id(),
        tenant_id=test_file_1.tenant_id(),
    )

    assert found_file is not None
    assert found_file["reference"] is not None
    assert found_file["reference"]["entity_type"] == ReferenceType.DOCUMENT.value
    assert found_file["reference"]["entity_id"] == entity_id
    assert found_file["reference"]["entity_name"] == entity_name


def test_file_of_id__without_reference__returns_null_reference(
    test_file_1,
    query_file_repository,
    add_single_file,
):
    add_single_file(test_file_1)

    found_file = query_file_repository.file_of_id(
        file_id=test_file_1.id(),
        tenant_id=test_file_1.tenant_id(),
    )

    assert found_file is not None
    assert found_file["reference"] is None
