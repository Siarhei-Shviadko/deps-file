import io
from uuid import uuid4

import pytest

from deps_file.constants import (
    BATCH_COMMANDS_CHANNEL,
    COMMANDS_CHANNEL,
    COMMANDS_REPLIES_CHANNEL,
    DOCUMENT_COMMANDS_CHANNEL,
    SPLIT_COMMANDS_CHANNEL,
)
from deps_file.domain.exceptions import (
    FileIsNotFailed,
    FileNotFound,
    FileReferenceAlreadyExists,
    GroupNotFound,
)
from deps_file.domain.model import (
    ClassifyFileDomain,
    ProcessFileDomain,
    ProcessingParamsDict,
    ReferenceType,
    TenantId,
)
from deps_file.domain.model.file import (
    FileProcessed,
    FileStateUpdated,
    Purpose,
    SplitFile,
    Status,
)
from deps_file.messaging.commands import DeleteBatchesWithDocuments, DeleteDocument
from tests.factories import FileFactory, ProcessingParamsFactory


def test_save_file__file_saved(command_file_service):
    file_bytes = b"Content of the file"
    file_like_object = io.BytesIO(file_bytes)
    file_like_object.name = "file.txt"

    workflow_params = ProcessingParamsFactory.create_processing_params().workflow_params
    tenant_id = "test_tenant_id"
    file_name = "test_file.ext"
    labels = ["test1", "test2"]

    file = command_file_service.process(
        tenant_id=tenant_id,
        name=file_name,
        content=file_like_object,
        workflow_params=workflow_params,
        labels=labels,
    )

    assert file.tenant_id == TenantId(tenant_id)
    assert file.name == file_name
    assert file.processing_params.workflow_params == workflow_params
    assert file.labels == labels

    [file_event] = file.events
    assert file_event.file_id == file.id()
    assert file_event.name == file.name
    assert file_event.path == file.path
    assert file_event.processing_params == ProcessingParamsDict(
        group_id=file.processing_params.group_id() if file.processing_params.group_id else None,
        splitting_enabled=file.processing_params.splitting_enabled,
        classification_enabled=file.processing_params.splitting_enabled,
        workflow_params=file.processing_params.workflow_params,  # type: ignore
    )


def test_classify__with_valid_group__creates_file_for_classification(
    command_file_service, command_group_service, basic_classify_params, fake
):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file_name = f"{fake.word()}_document.pdf"
    labels = [fake.word(), fake.word()]
    workflow_params = {"document_type_id": str(uuid4())}

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params=workflow_params,
        labels=labels,
    )

    assert file.tenant_id == TenantId(tenant_id)
    assert file.name == file_name
    assert file.processing_params.classification_enabled is True
    assert file.processing_params.splitting_enabled is False
    assert file.processing_params.group_id() == group_id
    assert len(file.labels) == 2
    assert labels[0] in file.labels
    assert labels[1] in file.labels


def test_classify__with_invalid_group__raises_group_not_found(command_file_service, fake):
    command_file_service._uow.groups.group_of_id = lambda group_id, tenant_id: None

    invalid_group_id = str(uuid4())
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    with pytest.raises(GroupNotFound) as exc_info:
        command_file_service.classify(
            tenant_id=tenant_id,
            name=file_name,
            content=b"content",
            group_id=invalid_group_id,
            workflow_params={"document_type_id": str(uuid4())},
            labels=[],
        )

    assert exc_info.value.code == "group_not_found"
    assert invalid_group_id in str(exc_info.value)


def test_classify__with_content__creates_file_correctly(command_file_service, command_group_service, fake):
    file_content = b"Test file content"
    file_name = f"{fake.word()}_document.pdf"
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    labels = [fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    result = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=file_content,
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=labels,
    )

    assert result.name == file_name
    assert result.processing_params.classification_enabled is True
    assert result.processing_params.splitting_enabled is False
    assert result.labels == labels
    assert result.path


def test_classify__sends_classify_command_with_correct_data(
    command_group_service, command_file_service, fake_command_producer, fake
):
    engine = fake.word()
    language = "en"
    workflow_params = {"engine": engine, "language": language}
    group_id = str(uuid4())
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    created_file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ClassifyFileDomain)
    assert command.file_id == str(created_file.id())
    assert command.file_name == file_name
    assert command.group_id == group_id
    assert command.engine == engine
    assert command.language == language


def test_classify__saves_file_with_labels(command_file_service, command_group_service, fake):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_invoice.pdf"
    labels = [fake.word(), fake.word(), fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    created_file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"invoice content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=labels,
    )

    saved_file = command_file_service._uow.files.file_of_id(str(created_file.id()), tenant_id)
    assert saved_file is not None
    assert saved_file.id() == created_file.id()

    assert len(created_file.labels) == 3
    assert labels[0] in created_file.labels
    assert labels[1] in created_file.labels
    assert labels[2] in created_file.labels


def test_classify__with_file_name_and_content__creates_file_correctly(
    command_file_service, command_group_service, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"PDF content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=[],
    )

    assert file.name == file_name
    assert file.processing_params.classification_enabled is True


def test_classify__with_no_labels__creates_file_without_labels(command_file_service, command_group_service, fake):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=[],
    )

    assert file.labels is None or len(file.labels) == 0


def test_classify__with_single_label__creates_file_with_one_label(command_file_service, command_group_service, fake):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    label = fake.word()

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=[label],
    )

    assert file.labels is not None
    assert len(file.labels) == 1
    assert label in file.labels


def test_classify__with_multiple_labels__creates_file_with_all_labels(
    command_file_service, command_group_service, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    labels = [fake.word(), fake.word(), fake.word(), fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=labels,
    )

    assert file.labels is not None
    assert len(file.labels) == 4
    for expected_label in labels:
        assert expected_label in file.labels


def test_classify__with_tenant_and_group__creates_file_for_correct_tenant(
    command_file_service, command_group_service, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=[],
    )

    assert file.tenant_id == TenantId(tenant_id)
    assert file.processing_params.group_id() == group_id


def test_classify__with_workflow_params__stores_correct_params(
    command_file_service, command_group_service, fake_command_producer, fake
):
    engine = fake.word()
    language = "en"
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    document_type_id = str(uuid4())
    workflow_params = {
        "document_type_id": document_type_id,
        "parsing_features": [],
        "needs_unifier": False,
        "needs_extraction": False,
        "assigned_to_me": False,
        "llm_type": None,
        "engine": engine,
        "language": language,
        "metadata": {},
    }
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL

    assert isinstance(command, ClassifyFileDomain)
    assert command.engine == engine
    assert command.language == language


def test_classify__with_content__uploads_to_storage(
    command_file_service, command_group_service, object_storage_mock, fake
):
    content = b"test file content"
    file_name = f"{fake.word()}_file.pdf"
    tenant_id = str(uuid4())
    group_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=content,
        group_id=group_id,
        workflow_params={"document_type_id": str(uuid4())},
        labels=[],
    )

    assert len(object_storage_mock._storage) == 1

    uploaded_path = list(object_storage_mock._storage.keys())[0]
    uploaded_content = object_storage_mock._storage[uploaded_path]

    assert uploaded_content == content
    assert uploaded_path.endswith(".pdf")
    assert len(uploaded_path) == 36  # 32 hex chars + 4 chars for file extension
    assert uploaded_path != file_name  # Should be unique


def test_classify__with_non_existent_group__raises_group_not_found(command_file_service, fake):
    command_file_service._uow.groups.group_of_id = lambda group_id, tenant_id: None

    non_existent_group_id = str(uuid4())
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    with pytest.raises(GroupNotFound) as exc_info:
        command_file_service.classify(
            tenant_id=tenant_id,
            name=file_name,
            content=b"content",
            group_id=non_existent_group_id,
            workflow_params={"document_type_id": str(uuid4())},
            labels=[],
        )

    assert exc_info.value.code == "group_not_found"


def test_split__with_valid_group__creates_file_for_splitting(
    command_file_service, command_group_service, basic_split_params, fake
):
    group_id = str(uuid4())
    tenant_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file_name = f"{fake.word()}_document.pdf"
    labels = [fake.word(), fake.word()]

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=False,
        workflow_params=basic_split_params,
        labels=labels,
    )

    assert file.tenant_id == TenantId(tenant_id)
    assert file.name == file_name
    assert file.processing_params.classification_enabled is False
    assert file.processing_params.splitting_enabled is True
    assert file.processing_params.group_id() == group_id
    assert len(file.labels) == 2
    assert labels[0] in file.labels
    assert labels[1] in file.labels


def test_split__with_invalid_group__raises_group_not_found(command_file_service, basic_split_params, fake):
    command_file_service._uow.groups.group_of_id = lambda group_id, tenant_id: None

    invalid_group_id = str(uuid4())
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    with pytest.raises(GroupNotFound) as exc_info:
        command_file_service.split(
            tenant_id=tenant_id,
            name=file_name,
            content=b"content",
            group_id=invalid_group_id,
            classification_enabled=True,
            workflow_params=basic_split_params,
            labels=[],
        )

    assert exc_info.value.code == "group_not_found"
    assert invalid_group_id in str(exc_info.value)


def test_split__with_content__creates_file_correctly(
    command_file_service, command_group_service, basic_split_params, fake
):
    file_content = b"Test file content"
    file_name = f"{fake.word()}_document.pdf"
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    labels = [fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    result = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=file_content,
        group_id=group_id,
        classification_enabled=False,
        workflow_params=basic_split_params,
        labels=labels,
    )

    assert result.name == file_name
    assert result.processing_params.classification_enabled is False
    assert result.processing_params.splitting_enabled is True
    assert result.labels == labels
    assert result.path


def test_split__sends_split_command_with_correct_data(
    command_group_service, command_file_service, fake_command_producer, fake
):
    engine = fake.word()
    language = "en"
    group_id = str(uuid4())
    tenant_id = str(uuid4())
    document_type_id = str(uuid4())
    workflow_params = {
        "document_type_id": document_type_id,
        "parsing_features": [],
        "needs_unifier": False,
        "needs_extraction": False,
        "assigned_to_me": False,
        "llm_type": None,
        "engine": engine,
        "language": language,
        "metadata": {},
    }
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    created_file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == SplitFile.COMMAND_CHANNEL
    assert reply_to == SplitFile.REPLY_CHANNEL
    assert isinstance(command, SplitFile)
    assert command.file_id == str(created_file.id())
    assert command.file_name == file_name
    assert command.group_id == group_id
    assert command.engine == engine
    assert command.language == language


def test_split__saves_file_with_labels(command_file_service, command_group_service, basic_split_params, fake):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_invoice.pdf"
    labels = [fake.word(), fake.word(), fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    created_file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"invoice content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=labels,
    )

    saved_file = command_file_service._uow.files.file_of_id(str(created_file.id()), tenant_id)
    assert saved_file is not None
    assert saved_file.id() == created_file.id()

    assert len(created_file.labels) == 3
    assert labels[0] in created_file.labels
    assert labels[1] in created_file.labels
    assert labels[2] in created_file.labels


def test_split__with_file_name_and_content__creates_file_correctly(
    command_file_service, command_group_service, basic_split_params, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"PDF content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=[],
    )

    assert file.name == file_name
    assert file.processing_params.classification_enabled is True


def test_split__with_no_labels__creates_file_without_labels(
    command_file_service, command_group_service, basic_split_params, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=[],
    )

    assert file.labels is None or len(file.labels) == 0


def test_split__with_single_label__creates_file_with_one_label(
    command_file_service, command_group_service, basic_split_params, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    label = fake.word()

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=[label],
    )

    assert file.labels is not None
    assert len(file.labels) == 1
    assert label in file.labels


def test_split__with_multiple_labels__creates_file_with_all_labels(
    command_file_service, command_group_service, basic_split_params, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    labels = [fake.word(), fake.word(), fake.word(), fake.word()]

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=labels,
    )

    assert file.labels is not None
    assert len(file.labels) == 4
    for expected_label in labels:
        assert expected_label in file.labels


def test_split__with_tenant_and_group__creates_file_for_correct_tenant(
    command_file_service, command_group_service, basic_split_params, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=[],
    )

    assert file.tenant_id == TenantId(tenant_id)
    assert file.processing_params.group_id() == group_id


def test_split__with_workflow_params__stores_correct_params(
    command_file_service, command_group_service, fake_command_producer, fake
):
    engine = fake.word()
    language = "en"
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    document_type_id = str(uuid4())
    workflow_params = {
        "document_type_id": document_type_id,
        "parsing_features": [],
        "needs_unifier": False,
        "needs_extraction": False,
        "assigned_to_me": False,
        "llm_type": None,
        "engine": engine,
        "language": language,
        "metadata": {},
    }
    file_name = f"{fake.word()}_document.pdf"

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=True,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == SplitFile.COMMAND_CHANNEL
    assert reply_to == SplitFile.REPLY_CHANNEL

    assert isinstance(command, SplitFile)
    assert command.engine == engine
    assert command.language == language


def test_split__with_content__uploads_to_storage(
    command_file_service, command_group_service, object_storage_mock, basic_split_params, fake
):
    content = b"test file content"
    file_name = f"{fake.word()}_file.pdf"
    tenant_id = str(uuid4())
    group_id = str(uuid4())

    command_group_service.create(
        group_id=group_id,
        tenant_id=tenant_id,
    )

    command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=content,
        group_id=group_id,
        classification_enabled=True,
        workflow_params=basic_split_params,
        labels=[],
    )

    assert len(object_storage_mock._storage) == 1

    uploaded_path = list(object_storage_mock._storage.keys())[0]
    uploaded_content = object_storage_mock._storage[uploaded_path]

    assert uploaded_content == content
    assert uploaded_path.endswith(".pdf")
    assert len(uploaded_path) == 36  # 32 hex chars + 4 chars for file extension
    assert uploaded_path != file_name  # Should be unique


def test_split__with_non_existent_group__raises_group_not_found(command_file_service, basic_split_params, fake):
    command_file_service._uow.groups.group_of_id = lambda group_id, tenant_id: None

    non_existent_group_id = str(uuid4())
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"

    with pytest.raises(GroupNotFound) as exc_info:
        command_file_service.split(
            tenant_id=tenant_id,
            name=file_name,
            content=b"content",
            group_id=non_existent_group_id,
            classification_enabled=True,
            workflow_params=basic_split_params,
            labels=[],
        )

    assert exc_info.value.code == "group_not_found"


def test_delete_files__with_valid_ids__deletes_files_successfully(command_file_service, test_file_1, test_file_2):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)
    files_repo.save(test_file_2)

    tenant_id = str(test_file_1.tenant_id())
    file_ids = {str(test_file_1.id()), str(test_file_2.id())}

    command_file_service.delete_files(ids=file_ids, tenant_id=tenant_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id) is None
    assert files_repo.file_of_id(str(test_file_2.id()), tenant_id) is None


def test_delete_files__with_single_file__deletes_file_successfully(command_file_service, test_file_1):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)

    tenant_id = str(test_file_1.tenant_id())
    file_ids = {str(test_file_1.id())}

    command_file_service.delete_files(ids=file_ids, tenant_id=tenant_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id) is None


def test_delete_files__with_empty_ids__does_nothing(command_file_service, test_file_1):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)

    tenant_id = str(test_file_1.tenant_id())
    original_file = files_repo.file_of_id(str(test_file_1.id()), tenant_id)

    command_file_service.delete_files(ids=set(), tenant_id=tenant_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id) is not None
    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id).id() == original_file.id()


def test_delete_files__with_non_existent_ids__does_nothing(command_file_service, test_file_1):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)

    tenant_id = str(test_file_1.tenant_id())
    non_existent_ids = {"non-existent-id-1", "non-existent-id-2"}

    command_file_service.delete_files(ids=non_existent_ids, tenant_id=tenant_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id) is not None


def test_delete_files__with_mixed_existing_and_non_existent_ids__deletes_only_existing(
    command_file_service, test_file_1, test_file_2
):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)
    files_repo.save(test_file_2)

    tenant_id = str(test_file_1.tenant_id())
    mixed_ids = {str(test_file_1.id()), "non-existent-id", str(test_file_2.id())}

    command_file_service.delete_files(ids=mixed_ids, tenant_id=tenant_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_id) is None
    assert files_repo.file_of_id(str(test_file_2.id()), tenant_id) is None


def test_delete_files__with_cross_tenant_files__only_deletes_own_tenant_files(
    command_file_service, test_file_1, test_file_2
):
    files_repo = command_file_service._uow.files
    files_repo.save(test_file_1)
    files_repo.save(test_file_2)

    tenant_1_id = str(test_file_1.tenant_id())
    tenant_2_id = str(test_file_2.tenant_id())
    file_ids = {str(test_file_1.id()), str(test_file_2.id())}

    command_file_service.delete_files(ids=file_ids, tenant_id=tenant_1_id)

    assert files_repo.file_of_id(str(test_file_1.id()), tenant_1_id) is None
    assert files_repo.file_of_id(str(test_file_2.id()), tenant_2_id) is not None


def test_delete_files__calls_repository_methods_correctly(command_file_service, test_file_1, test_file_2, mocker):
    mock_files_repo = mocker.Mock()
    mock_files_repo.files_of_ids.return_value = [test_file_1, test_file_2]
    command_file_service._uow.files = mock_files_repo

    mock_commit = mocker.Mock()
    command_file_service._uow.commit = mock_commit

    tenant_id = str(test_file_1.tenant_id())
    file_ids = {str(test_file_1.id()), str(test_file_2.id())}

    command_file_service.delete_files(ids=file_ids, tenant_id=tenant_id)

    mock_files_repo.files_of_ids.assert_called_once_with(file_ids, tenant_id)
    mock_files_repo.delete_all.assert_called_once_with([test_file_1, test_file_2])
    mock_commit.assert_called_once()


def test_delete_files__with_no_files_found__does_not_call_delete_all(command_file_service, mocker):
    mock_files_repo = mocker.Mock()
    mock_files_repo.files_of_ids.return_value = []
    command_file_service._uow.files = mock_files_repo

    mock_commit = mocker.Mock()
    command_file_service._uow.commit = mock_commit

    tenant_id = "test_tenant"
    file_ids = {"non-existent-id"}

    command_file_service.delete_files(ids=file_ids, tenant_id=tenant_id)

    mock_files_repo.files_of_ids.assert_called_once_with(file_ids, tenant_id)
    mock_files_repo.delete_all.assert_not_called()
    mock_commit.assert_not_called()


def test_classify_file__with_document_reference__raises_file_reference_already_exists(
    command_file_service, command_group_service, test_file_1
):
    file_id = str(test_file_1.id())
    tenant_id = str(test_file_1.tenant_id())
    group_id = str(uuid4())

    test_file_1._add_reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Existing Document",
    )

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)
    command_file_service._uow.files.save(test_file_1)

    workflow_params = {"engine": "tesseract", "language": "eng"}

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        command_file_service.classify_file(
            file_id=file_id,
            tenant_id=tenant_id,
            group_id=group_id,
            workflow_params=workflow_params,
        )

    assert exc_info.value.code == "file_reference_already_exists"
    assert file_id in str(exc_info.value)


def test_classify_file__with_batch_reference__raises_file_reference_already_exists(
    command_file_service, command_group_service, test_file_1
):
    file_id = str(test_file_1.id())
    tenant_id = str(test_file_1.tenant_id())
    group_id = str(uuid4())

    test_file_1._add_reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Existing Batch",
    )

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)
    command_file_service._uow.files.save(test_file_1)

    workflow_params = {"engine": "tesseract", "language": "eng"}

    with pytest.raises(FileReferenceAlreadyExists) as exc_info:
        command_file_service.classify_file(
            file_id=file_id,
            tenant_id=tenant_id,
            group_id=group_id,
            workflow_params=workflow_params,
        )

    assert exc_info.value.code == "file_reference_already_exists"
    assert file_id in str(exc_info.value)


def test_send_commands__process_file__sends_process_file_command_correctly(
    command_file_service, fake_command_producer, fake
):
    tenant_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    workflow_params = {
        "engine": "tesseract",
        "language": "eng",
        "parsing_features": ["text"],
    }

    created_file = command_file_service.process(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ProcessFileDomain)
    assert command.file_id == str(created_file.id())
    assert command.files == [created_file.path]
    assert command.tenant_id == tenant_id
    assert command.engine == workflow_params["engine"]
    assert command.language == workflow_params["language"]
    assert command.parsing_features == workflow_params["parsing_features"]


def test_send_commands__classify_file__sends_classify_file_domain_command_correctly(
    command_file_service, command_group_service, fake_command_producer, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    engine = fake.word()
    language = "en"
    workflow_params = {
        "engine": engine,
        "language": language,
        "parsing_features": ["tables"],
        "llm_type": "gpt-4",
        "needs_unifier": True,
        "needs_extraction": False,
        "assigned_to_me": True,
        "metadata": {"key": "value"},
    }

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)

    created_file = command_file_service.classify(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ClassifyFileDomain)
    assert command.file_id == str(created_file.id())
    assert command.file_name == file_name
    assert command.path == created_file.path
    assert command.group_id == group_id
    assert command.engine == engine
    assert command.language == language
    assert command.parsing_features == workflow_params["parsing_features"]
    assert command.llm_type == workflow_params["llm_type"]
    assert command.needs_unifier == workflow_params["needs_unifier"]
    assert command.needs_extraction == workflow_params["needs_extraction"]
    assert command.assigned_to_me == workflow_params["assigned_to_me"]
    assert command.metadata == workflow_params["metadata"]


def test_send_commands__classify_file_existing__sends_classify_file_domain_command_correctly(
    command_file_service, command_group_service, fake_command_producer
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    initial_workflow_params = {
        "engine": "AWS_TEXTRACT",
        "language": "en",
        "parsing_features": [],
        "needs_unifier": False,
        "needs_extraction": False,
        "assigned_to_me": False,
    }

    new_engine = "tesseract"
    new_language = "eng"
    new_workflow_params = {
        "engine": new_engine,
        "language": new_language,
        "parsing_features": ["text"],
        "needs_unifier": True,
        "needs_extraction": False,
        "assigned_to_me": True,
    }

    test_file = FileFactory.create_for_classification(
        tenant_id=tenant_id, workflow_params=initial_workflow_params, group_id=group_id
    )
    file_id = str(test_file.id())

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)
    command_file_service._uow.files.save(test_file)

    command_file_service.classify_file(
        file_id=file_id,
        tenant_id=tenant_id,
        group_id=group_id,
        workflow_params=new_workflow_params,
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ClassifyFileDomain)
    assert command.file_id == file_id
    assert command.file_name == test_file.name
    assert command.path == test_file.path
    assert command.group_id == group_id
    assert command.engine == new_engine
    assert command.language == new_language
    assert command.parsing_features == new_workflow_params["parsing_features"]
    assert command.needs_unifier == new_workflow_params["needs_unifier"]
    assert command.needs_extraction == new_workflow_params["needs_extraction"]
    assert command.assigned_to_me == new_workflow_params["assigned_to_me"]


def test_send_commands__split_file__sends_split_file_domain_command_correctly(
    command_file_service, command_group_service, fake_command_producer, fake
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    file_name = f"{fake.word()}_document.pdf"
    document_type_id = str(uuid4())
    engine = fake.word()
    language = "en"
    classification_enabled = True
    workflow_params = {
        "document_type_id": document_type_id,
        "engine": engine,
        "language": language,
        "parsing_features": ["tables"],
        "llm_type": "gpt-4",
        "needs_unifier": False,
        "needs_extraction": True,
        "assigned_to_me": False,
        "metadata": {"key": "value"},
    }

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)

    created_file = command_file_service.split(
        tenant_id=tenant_id,
        name=file_name,
        content=b"content",
        group_id=group_id,
        classification_enabled=classification_enabled,
        workflow_params=workflow_params,
        labels=[],
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == SplitFile.COMMAND_CHANNEL
    assert reply_to == SplitFile.REPLY_CHANNEL
    assert isinstance(command, SplitFile)
    assert command.file_id == str(created_file.id())
    assert command.file_name == file_name
    assert command.path == created_file.path
    assert command.group_id == group_id
    assert command.classification_enabled == classification_enabled
    assert command.document_type_id == document_type_id
    assert command.engine == engine
    assert command.language == language
    assert command.parsing_features == workflow_params["parsing_features"]
    assert command.llm_type == workflow_params["llm_type"]
    assert command.needs_unifier == workflow_params["needs_unifier"]
    assert command.needs_extraction == workflow_params["needs_extraction"]
    assert command.assigned_to_me == workflow_params["assigned_to_me"]
    assert command.metadata == workflow_params["metadata"]


def test_send_commands__split_file_existing__sends_split_file_domain_command_correctly(
    command_file_service, command_group_service, fake_command_producer
):
    tenant_id = str(uuid4())
    group_id = str(uuid4())
    initial_classification_enabled = False
    initial_workflow_params = {
        "document_type_id": str(uuid4()),
        "engine": "AWS_TEXTRACT",
        "language": "en",
        "parsing_features": [],
    }

    new_classification_enabled = True
    new_engine = "tesseract"
    new_language = "eng"
    new_workflow_params = {
        "document_type_id": str(uuid4()),
        "engine": new_engine,
        "language": new_language,
        "parsing_features": ["text"],
    }

    test_file = FileFactory.create_for_splitting(
        tenant_id=tenant_id,
        group_id=group_id,
        classification_enabled=initial_classification_enabled,
        workflow_params=initial_workflow_params,
    )
    file_id = str(test_file.id())

    command_group_service.create(group_id=group_id, tenant_id=tenant_id)
    command_file_service._uow.files.save(test_file)

    command_file_service.split_file(
        file_id=file_id,
        tenant_id=tenant_id,
        group_id=group_id,
        classification_enabled=new_classification_enabled,
        workflow_params=new_workflow_params,
    )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]

    assert channel == SplitFile.COMMAND_CHANNEL
    assert reply_to == SplitFile.REPLY_CHANNEL
    assert isinstance(command, SplitFile)
    assert command.file_id == file_id
    assert command.file_name == test_file.name
    assert command.path == test_file.path
    assert command.group_id == group_id
    assert command.classification_enabled == new_classification_enabled
    assert command.engine == new_engine
    assert command.language == new_language
    assert command.parsing_features == new_workflow_params["parsing_features"]
    assert command.document_type_id == new_workflow_params["document_type_id"]


@pytest.mark.usefixtures("save_file")
def test_create_document_from_file__with_valid_file__creates_document_and_saves_reference(
    command_file_service,
    fake_unit_of_work,
    fake_document_proxy,
    object_storage_mock,
    tenant_id,
    document_type_id,
    test_file_1,
    file_path,
    file_name,
):
    file_content = b"test file content"

    object_storage_mock._storage[file_path] = file_content

    result_document_id, result_document_name = command_file_service.create_document_from_file(
        file_id=str(test_file_1.id()),
        tenant_id=tenant_id(),
        document_type_id=document_type_id,
    )

    assert result_document_id is not None
    assert result_document_name == file_name

    assert len(fake_document_proxy.documents) == 1
    created_doc = fake_document_proxy.documents[0]
    assert created_doc["file_name"] == file_name
    assert created_doc["file_content"] == file_content
    assert created_doc["document_type_id"] == document_type_id
    assert created_doc["group_id"] is None

    with fake_unit_of_work:
        saved_file = fake_unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_id())
        assert saved_file is not None
        assert saved_file.reference is not None
        assert saved_file.reference.entity_id == result_document_id
        assert saved_file.reference.entity_name == result_document_name


def test_create_document_from_file__with_existing_reference__raises_file_reference_already_exists(
    command_file_service,
    fake_unit_of_work,
    fake_document_proxy,
    tenant_id,
    document_type_id,
    file_path,
    file_name,
    test_workflow_params,
):
    existing_document_id = str(uuid4())
    existing_document_name = "existing_document.pdf"

    file = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        group_id=None,
        workflow_params=test_workflow_params,
    )
    file.complete_classification(existing_document_id, existing_document_name)

    with fake_unit_of_work:
        fake_unit_of_work.files.save(file)
        fake_unit_of_work.commit()

    with pytest.raises(FileReferenceAlreadyExists):
        command_file_service.create_document_from_file(
            file_id=str(file.id()),
            tenant_id=tenant_id(),
            document_type_id=document_type_id,
        )

    assert len(fake_document_proxy.documents) == 0


def test_create_document_from_file__with_non_existent_file__raises_file_not_found(
    command_file_service, tenant_id, test_file_1_id, document_type_id
):
    with pytest.raises(FileNotFound):
        command_file_service.create_document_from_file(
            file_id=test_file_1_id(),
            tenant_id=tenant_id(),
            document_type_id=document_type_id,
        )


@pytest.mark.usefixtures("save_file")
def test_create_document_from_file__when_reference_save_fails__sends_delete_command(
    command_file_service,
    object_storage_mock,
    fake_command_producer,
    tenant_id,
    document_type_id,
    file_path,
    test_file_1,
    mocker,
):
    file_content = b"test file content"

    object_storage_mock._storage[file_path] = file_content

    mocker.patch.object(command_file_service, "_save_document_reference", side_effect=Exception("Save failed"))

    with pytest.raises(Exception, match="Save failed"):
        command_file_service.create_document_from_file(
            file_id=str(test_file_1.id()),
            tenant_id=tenant_id(),
            document_type_id=document_type_id,
        )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == DOCUMENT_COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, DeleteDocument)
    assert command.document_id is not None


@pytest.mark.usefixtures("save_file")
def test_create_batch_from_file__with_valid_file__creates_batch_and_saves_reference(
    command_file_service,
    fake_unit_of_work,
    fake_batch_proxy,
    tenant_id,
    batch_id,
    batch_name,
    file_info_params,
    test_file_1,
    test_workflow_params,
    test_group_1_id,
):
    file_id = test_file_1.id()
    result_batch_id = command_file_service.create_batch_from_file(
        file_id=file_id,
        tenant_id=tenant_id(),
        batch_name=batch_name,
        batch_files=file_info_params,
        group_id=test_group_1_id(),
    )

    assert result_batch_id == batch_id

    assert len(fake_batch_proxy.batches) == 1
    created_batch = fake_batch_proxy.batches[0]
    assert created_batch["batch_name"] == batch_name
    assert created_batch["files"] == file_info_params
    assert created_batch["group_id"] == test_group_1_id()
    assert created_batch["engine"] == test_workflow_params.get("engine")
    assert created_batch["language"] == test_workflow_params.get("language")
    assert created_batch["llm_type"] == test_workflow_params.get("llm_type")
    assert created_batch["parsing_features"] == test_workflow_params.get("parsing_features")
    assert created_batch["source_file_id"] == file_id

    with fake_unit_of_work:
        saved_file = fake_unit_of_work.files.file_of_id(str(test_file_1.id()), tenant_id())
        assert saved_file is not None
        assert saved_file.reference is not None
        assert saved_file.reference.entity_id == batch_id
        assert saved_file.reference.entity_name == batch_name


def test_create_batch_from_file__with_existing_reference__raises_file_reference_already_exists(
    command_file_service,
    fake_unit_of_work,
    fake_batch_proxy,
    tenant_id,
    batch_name,
    file_path,
    file_name,
    file_info_params,
    test_workflow_params,
    test_group_1_id,
):
    existing_batch_id = str(uuid4())
    existing_batch_name = "existing_batch"

    file = FileFactory.create_for_processing(
        tenant_id=tenant_id(),
        name=file_name,
        path=file_path,
        group_id=None,
        workflow_params=test_workflow_params,
    )
    file.complete_splitting(entity_id=existing_batch_id, entity_name=existing_batch_name)

    with fake_unit_of_work:
        fake_unit_of_work.files.save(file)
        fake_unit_of_work.commit()

    with pytest.raises(FileReferenceAlreadyExists):
        command_file_service.create_batch_from_file(
            file_id=str(file.id()),
            tenant_id=tenant_id(),
            batch_name=batch_name,
            batch_files=file_info_params,
            group_id=test_group_1_id(),
        )

    assert len(fake_batch_proxy.batches) == 0


def test_create_batch_from_file__with_non_existent_file__raises_file_not_found(
    command_file_service,
    tenant_id,
    test_file_1_id,
    batch_name,
    file_info_params,
    test_group_1_id,
):
    with pytest.raises(FileNotFound):
        command_file_service.create_batch_from_file(
            file_id=test_file_1_id(),
            tenant_id=tenant_id(),
            batch_name=batch_name,
            batch_files=file_info_params,
            group_id=test_group_1_id(),
        )


@pytest.mark.usefixtures("save_file")
def test_create_batch_from_file__when_reference_save_fails__sends_delete_command(
    command_file_service,
    fake_command_producer,
    tenant_id,
    batch_id,
    batch_name,
    test_file_1,
    file_info_params,
    mocker,
    test_group_1_id,
):
    mocker.patch.object(command_file_service, "_save_batch_reference", side_effect=Exception("Save failed"))

    with pytest.raises(Exception, match="Save failed"):
        command_file_service.create_batch_from_file(
            file_id=str(test_file_1.id()),
            tenant_id=tenant_id(),
            batch_name=batch_name,
            batch_files=file_info_params,
            group_id=test_group_1_id(),
        )

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == BATCH_COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, DeleteBatchesWithDocuments)
    assert batch_id in command.batch_ids


@pytest.mark.usefixtures("save_test_file_for_processing")
def test_restart_file__without_failed_file__raises_file_is_not_failed(
    command_file_service,
    tenant_id,
    test_file_for_processing,
):
    with pytest.raises(FileIsNotFailed):
        command_file_service.restart_file(str(test_file_for_processing.id()), tenant_id())


@pytest.mark.usefixtures("save_test_failed_file_for_processing")
def test_restart_file__with_failed_file__resends_processing_command(
    command_file_service,
    fake_command_producer,
    tenant_id,
    test_file_for_processing,
):
    command_file_service.restart_file(str(test_file_for_processing.id()), tenant_id())

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ProcessFileDomain)
    assert command.file_id == str(test_file_for_processing.id())
    assert command.files == [test_file_for_processing.path]
    assert command.tenant_id == tenant_id()


@pytest.mark.usefixtures("save_test_failed_file_for_classification", "save_group")
def test_restart_file__with_failed_file__resends_classification_command(
    command_file_service,
    fake_command_producer,
    tenant_id,
    test_file_for_classification,
):
    command_file_service.restart_file(str(test_file_for_classification.id()), tenant_id())

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == COMMANDS_CHANNEL
    assert reply_to == COMMANDS_REPLIES_CHANNEL
    assert isinstance(command, ClassifyFileDomain)
    assert command.file_id == str(test_file_for_classification.id())
    assert command.file_name == test_file_for_classification.name
    assert command.group_id == test_file_for_classification.processing_params.group_id()
    assert command.engine == test_file_for_classification.processing_params.workflow_params["engine"]
    assert command.language == test_file_for_classification.processing_params.workflow_params["language"]
    assert (
        command.parsing_features == test_file_for_classification.processing_params.workflow_params["parsing_features"]
    )
    assert command.llm_type == test_file_for_classification.processing_params.workflow_params["llm_type"]
    assert command.needs_unifier == test_file_for_classification.processing_params.workflow_params["needs_unifier"]
    assert (
        command.needs_extraction == test_file_for_classification.processing_params.workflow_params["needs_extraction"]
    )
    assert command.assigned_to_me == test_file_for_classification.processing_params.workflow_params["assigned_to_me"]
    assert command.metadata == test_file_for_classification.processing_params.workflow_params["metadata"]


@pytest.mark.usefixtures("save_test_failed_file_for_splitting", "save_group")
def test_restart_file__with_failed_file__resends_splitting_command(
    command_file_service,
    fake_command_producer,
    tenant_id,
    test_file_for_splitting,
):
    command_file_service.restart_file(str(test_file_for_splitting.id()), tenant_id())

    assert len(fake_command_producer.sent_commands) == 1
    channel, command, reply_to = fake_command_producer.sent_commands[0]
    assert channel == SplitFile.COMMAND_CHANNEL
    assert reply_to == SplitFile.REPLY_CHANNEL
    assert isinstance(command, SplitFile)
    assert command.file_id == str(test_file_for_splitting.id())
    assert command.file_name == test_file_for_splitting.name
    assert command.path == test_file_for_splitting.path
    assert command.group_id == test_file_for_splitting.processing_params.group_id()
    assert command.classification_enabled == test_file_for_splitting.processing_params.classification_enabled
    assert command.document_type_id == test_file_for_splitting.processing_params.workflow_params["document_type_id"]
    assert command.engine == test_file_for_splitting.processing_params.workflow_params["engine"]
    assert command.language == test_file_for_splitting.processing_params.workflow_params["language"]
    assert command.parsing_features == test_file_for_splitting.processing_params.workflow_params["parsing_features"]
    assert command.llm_type == test_file_for_splitting.processing_params.workflow_params["llm_type"]
    assert command.needs_unifier == test_file_for_splitting.processing_params.workflow_params["needs_unifier"]
    assert command.needs_extraction == test_file_for_splitting.processing_params.workflow_params["needs_extraction"]
    assert command.assigned_to_me == test_file_for_splitting.processing_params.workflow_params["assigned_to_me"]
    assert command.metadata == test_file_for_splitting.processing_params.workflow_params["metadata"]


@pytest.mark.usefixtures("save_test_file_for_processing")
def test_complete_processing__with_valid_file__publishes_file_processed_event(
    command_file_service,
    tenant_id,
    test_file_for_processing,
    fake_domain_event_publisher,
):
    command_file_service.complete_processing(str(test_file_for_processing.id()), tenant_id())

    event = fake_domain_event_publisher.last_published.events[-1]
    assert isinstance(event, FileProcessed)
    assert event.id == str(test_file_for_processing.id())
    assert event.status == Status.COMPLETED.value
    assert event.purpose == Purpose.PROCESSING.value
    assert event.metadata == test_file_for_processing.processing_params.workflow_params["metadata"]
    assert event.error_message is None


@pytest.mark.usefixtures("save_test_file_for_processing")
def test_fail_processing__with_valid_file__publishes_file_processed_event(
    command_file_service,
    tenant_id,
    test_file_for_processing,
    error_message,
    fake_domain_event_publisher,
):
    command_file_service.fail_processing(str(test_file_for_processing.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[-1]
    assert isinstance(event, FileProcessed)
    assert event.id == str(test_file_for_processing.id())
    assert event.status == Status.FAILED.value
    assert event.purpose == Purpose.PROCESSING.value
    assert event.metadata == test_file_for_processing.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_classification")
def test_complete_classification__with_valid_file__publishes_file_processed_event(
    command_file_service,
    tenant_id,
    test_file_for_classification,
    fake_domain_event_publisher,
    error_message,
):
    command_file_service.fail_classification(str(test_file_for_classification.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[-1]
    assert isinstance(event, FileProcessed)
    assert event.id == str(test_file_for_classification.id())
    assert event.status == Status.FAILED.value
    assert event.purpose == Purpose.CLASSIFICATION.value
    assert event.metadata == test_file_for_classification.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_splitting")
def test_complete_splitting__with_valid_file__publishes_file_processed_event(
    command_file_service,
    tenant_id,
    test_file_for_splitting,
    fake_domain_event_publisher,
    error_message,
):
    command_file_service.fail_splitting(str(test_file_for_splitting.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[-1]
    assert isinstance(event, FileProcessed)
    assert event.id == str(test_file_for_splitting.id())
    assert event.status == Status.FAILED.value
    assert event.purpose == Purpose.SPLITTING.value
    assert event.metadata == test_file_for_splitting.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_processing")
def test_complete_processing__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_processing,
    fake_domain_event_publisher,
):
    command_file_service.complete_processing(str(test_file_for_processing.id()), tenant_id())

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_processing.id())
    assert event.state == Status.COMPLETED.value
    assert event.metadata == test_file_for_processing.processing_params.workflow_params["metadata"]


@pytest.mark.usefixtures("save_test_file_for_processing")
def test_fail_processing__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_processing,
    error_message,
    fake_domain_event_publisher,
):
    command_file_service.fail_processing(str(test_file_for_processing.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_processing.id())
    assert event.state == Status.FAILED.value
    assert event.metadata == test_file_for_processing.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_classification")
def test_complete_classification__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_classification,
    fake_domain_event_publisher,
    document_id,
    document_name,
    document_type_id,
):
    command_file_service.complete_classification(
        str(test_file_for_classification.id()), tenant_id(), document_id, document_name, document_type_id
    )

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_classification.id())
    assert event.state == Status.COMPLETED.value
    assert event.metadata == test_file_for_classification.processing_params.workflow_params["metadata"]


@pytest.mark.usefixtures("save_test_file_for_classification")
def test_fail_classification__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_classification,
    fake_domain_event_publisher,
    error_message,
):
    command_file_service.fail_classification(str(test_file_for_classification.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_classification.id())
    assert event.state == Status.FAILED.value
    assert event.metadata == test_file_for_classification.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_splitting")
def test_complete_splitting__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_splitting,
    fake_domain_event_publisher,
    batch_id,
    batch_name,
):
    command_file_service.complete_splitting(str(test_file_for_splitting.id()), tenant_id(), batch_id, batch_name)

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_splitting.id())
    assert event.state == Status.COMPLETED.value
    assert event.metadata == test_file_for_splitting.processing_params.workflow_params["metadata"]


@pytest.mark.usefixtures("save_test_file_for_splitting")
def test_fail_splitting__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_splitting,
    fake_domain_event_publisher,
    error_message,
):
    command_file_service.fail_splitting(str(test_file_for_splitting.id()), tenant_id(), error_message)

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_splitting.id())
    assert event.state == Status.FAILED.value
    assert event.metadata == test_file_for_splitting.processing_params.workflow_params["metadata"]
    assert event.error_message == error_message


@pytest.mark.usefixtures("save_test_file_for_splitting")
def test_set_splitting_review__publishes_file_state_updated_event(
    command_file_service,
    tenant_id,
    test_file_for_splitting,
    fake_domain_event_publisher,
):
    command_file_service.set_splitting_review(str(test_file_for_splitting.id()), tenant_id())

    event = fake_domain_event_publisher.last_published.events[0]
    assert isinstance(event, FileStateUpdated)
    assert event.file_id == str(test_file_for_splitting.id())
    assert event.state == Status.SPLITTING_REVIEW.value


def test_set_splitting_review__with_nonexistent_file__raises_file_not_found(
    command_file_service,
    tenant_id,
):
    with pytest.raises(FileNotFound):
        command_file_service.set_splitting_review(str(uuid4()), tenant_id())
