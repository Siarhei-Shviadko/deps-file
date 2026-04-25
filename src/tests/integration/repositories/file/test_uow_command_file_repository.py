from uuid import uuid4

from deps_file.domain.model.file.constants import (
    MAX_FILE_NAME_LENGTH,
    MAX_FILE_PATH_LENGTH,
)
from deps_file.domain.model.file.reference import ReferenceType
from tests.shared_fixtures.file import (
    test_file_1,
    test_file_1_tenant_id,
    test_file_2,
    test_file_2_tenant_id,
)


def test_find_file(test_file_1, unit_of_work, add_single_file):
    add_single_file(test_file_1)

    with unit_of_work:
        found_file = unit_of_work.files.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())

    assert found_file is not None
    assert found_file.id == test_file_1.id
    assert found_file.tenant_id == test_file_1.tenant_id
    assert found_file.name == test_file_1.name
    assert found_file.path == test_file_1.path


def test_find_file__not_found(unit_of_work, test_file_1_tenant_id):
    with unit_of_work:
        result = unit_of_work.files.file_of_id(id_=uuid4().hex, tenant_id=test_file_1_tenant_id())

    assert result is None


def test_find_file__wrong_tenant(test_file_1, test_file_2_tenant_id, unit_of_work, add_single_file):
    add_single_file(test_file_1)

    with unit_of_work:
        result = unit_of_work.files.file_of_id(id_=test_file_1.id(), tenant_id=test_file_2_tenant_id())

    assert result is None


def test_save__new_file(test_file_1, unit_of_work, query_file_repository):
    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    found_file = query_file_repository.file_of_id(file_id=test_file_1.id(), tenant_id=test_file_1.tenant_id())

    assert found_file is not None
    assert found_file["file_id"] == test_file_1.id()
    assert found_file["name"] == test_file_1.name
    assert found_file["labels"]
    assert len(found_file["labels"]) == 1
    assert found_file["labels"][0] == "test_label"


def test_save__update_existing_file(test_file_1, unit_of_work, query_file_repository, add_single_file):
    add_single_file(test_file_1)

    test_file_1.name = "updated_name.pdf"
    test_file_1.path = "/updated/path/updated_name.pdf"

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    found_file = query_file_repository.file_of_id(file_id=test_file_1.id(), tenant_id=test_file_1.tenant_id())

    assert found_file["name"] == "updated_name.pdf"
    assert found_file["path"] == "/updated/path/updated_name.pdf"


def test_save__multiple_files(test_file_1, test_file_2, unit_of_work, query_file_repository):
    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.files.save(test_file_2)
        unit_of_work.commit()

    file_1 = query_file_repository.file_of_id(file_id=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    file_2 = query_file_repository.file_of_id(file_id=test_file_2.id(), tenant_id=test_file_2.tenant_id())

    assert file_1 is not None
    assert file_2 is not None
    assert file_1["file_id"] == test_file_1.id()
    assert file_2["file_id"] == test_file_2.id()


def test_save__with_complete_data(integration_file_with_complete_data, unit_of_work, query_file_repository):
    file = integration_file_with_complete_data

    with unit_of_work:
        unit_of_work.files.save(file)
        unit_of_work.commit()

    found_file = query_file_repository.file_of_id(file_id=file.id(), tenant_id=file.tenant_id())

    assert found_file["state"]["status"] == file.state.status.value
    expected_group_id = getattr(file.processing_params.group_id, "value", file.processing_params.group_id)
    assert found_file["processing_params"].get("group_id") == expected_group_id
    assert found_file["processing_params"].get("splitting_enabled") == file.processing_params.splitting_enabled


def test_save__with_minimal_data(integration_file_with_minimal_data, unit_of_work, query_file_repository):
    file = integration_file_with_minimal_data

    with unit_of_work:
        unit_of_work.files.save(file)
        unit_of_work.commit()

    found_file = query_file_repository.file_of_id(file_id=file.id(), tenant_id=file.tenant_id())

    assert found_file is not None
    assert found_file["processing_params"].get("group_id") is None


def test_save__max_database_limits(integration_file_max_database_limits, unit_of_work, query_file_repository):
    file = integration_file_max_database_limits

    with unit_of_work:
        unit_of_work.files.save(file)
        unit_of_work.commit()

    found_file = query_file_repository.file_of_id(file_id=file.id(), tenant_id=file.tenant_id())

    assert found_file is not None
    assert len(found_file["name"]) == MAX_FILE_NAME_LENGTH
    assert len(found_file["path"]) == MAX_FILE_PATH_LENGTH


def test_rollback(test_file_1, unit_of_work, query_file_repository):
    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.rollback()

    found_file = query_file_repository.file_of_id(file_id=test_file_1.id(), tenant_id=test_file_1.tenant_id())

    assert found_file is None


def test_tenant_isolation(integration_multi_tenant_files, unit_of_work, query_file_repository):
    file_1, file_2 = integration_multi_tenant_files

    with unit_of_work:
        unit_of_work.files.save(file_1)
        unit_of_work.files.save(file_2)
        unit_of_work.commit()

    found_1 = query_file_repository.file_of_id(file_id=file_1.id(), tenant_id=file_1.tenant_id())
    found_2 = query_file_repository.file_of_id(file_id=file_2.id(), tenant_id=file_2.tenant_id())

    cross_tenant = query_file_repository.file_of_id(file_id=file_1.id(), tenant_id=file_2.tenant_id())

    assert found_1 is not None
    assert found_2 is not None
    assert cross_tenant is None


def test_save__file_with_reference__persists_reference(
    unit_of_work,
    test_file_1,
):
    entity_id = str(uuid4())
    entity_name = "Test Document"

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )

    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    with unit_of_work:
        loaded_file = unit_of_work.files.file_of_id(
            str(test_file_1.id()),
            str(test_file_1.tenant_id()),
        )

    assert loaded_file is not None
    assert loaded_file.reference is not None
    assert loaded_file.reference.entity_type == ReferenceType.DOCUMENT
    assert loaded_file.reference.entity_id == entity_id
    assert loaded_file.reference.entity_name == entity_name


def test_save__file_without_reference__saves_successfully(
    unit_of_work,
    test_file_1,
):
    with unit_of_work:
        unit_of_work.files.save(test_file_1)
        unit_of_work.commit()

    with unit_of_work:
        loaded_file = unit_of_work.files.file_of_id(
            str(test_file_1.id()),
            str(test_file_1.tenant_id()),
        )

    assert loaded_file is not None
    assert loaded_file.reference is None
