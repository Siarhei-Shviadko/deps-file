import io

from deps_file.domain.model import TenantId
from tests.factories import ProcessingParamsFactory


def test_save_file__file_saved(command_file_service, query_file_repository):
    file_bytes = b"Content of the file"
    file_like_object = io.BytesIO(file_bytes)
    file_like_object.name = "file.txt"

    workflow_params = ProcessingParamsFactory.create_processing_params().workflow_params
    tenant_id = "test_tenant_id"
    file_name = "test_file"
    labels = ["test3", "test4", "test5"]

    file = command_file_service.process(
        tenant_id=tenant_id,
        name=file_name,
        content=file_like_object,
        workflow_params=workflow_params,
        labels=labels,
    )
    found_file = query_file_repository.find_file(file_id=file.id(), tenant_id=tenant_id)
    assert found_file["tenant_id"] == tenant_id
    assert found_file["name"] == file_name
    assert found_file["processing_params"]["workflow_params"] == workflow_params
    assert found_file["labels"] == labels

    [file_created_event] = file.events
    assert file_created_event.file_id == found_file["file_id"]
    assert file_created_event.name == found_file["name"]
    assert file_created_event.path == found_file["path"]
    assert not file_created_event.processing_params["group_id"]
    assert (
        file_created_event.processing_params["splitting_enabled"]
        == found_file["processing_params"]["splitting_enabled"]
    )
    assert (
        file_created_event.processing_params["classification_enabled"]
        == found_file["processing_params"]["classification_enabled"]
    )
    assert file_created_event.processing_params["workflow_params"] == found_file["processing_params"]["workflow_params"]
