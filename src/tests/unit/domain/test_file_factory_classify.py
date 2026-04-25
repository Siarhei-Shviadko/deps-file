import pytest

from deps_file.domain.model.file.file_factory import FileFactory
from deps_file.domain.model.file.state import Status


def test_create_for_classification__creates_file_with_correct_params(fake):
    tenant_id = fake.uuid4()
    name = f"{fake.word()}_document.pdf"
    path = f"/storage/{fake.word()}_document.pdf"
    group_id = fake.uuid4()
    workflow_params = {"engine": fake.word(), "language": "en"}
    labels = [fake.word(), fake.word()]

    file = FileFactory.create_for_classification(
        tenant_id=tenant_id, name=name, path=path, group_id=group_id, workflow_params=workflow_params, labels=labels
    )

    assert file.tenant_id.value == tenant_id
    assert file.name == name
    assert file.path == path
    assert file.processing_params.group_id() == group_id
    assert file.processing_params.workflow_params == workflow_params
    assert len(file.labels) == 2
    assert file.state.status == Status.PROCESSING


def test_create_for_classification__sets_classification_enabled_true(fake):
    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name=f"{fake.word()}.pdf",
        path=f"/path/{fake.word()}.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    assert file.processing_params.classification_enabled is True
    assert file.processing_params.splitting_enabled is False


def test_create_for_classification__sets_splitting_enabled_false(fake):
    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name=f"{fake.word()}.pdf",
        path=f"/path/{fake.word()}.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    assert file.processing_params.splitting_enabled is False


def test_create_for_classification__handles_none_labels(fake):
    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name=f"{fake.word()}.pdf",
        path=f"/path/{fake.word()}.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=None,
    )

    assert file.labels is None or file.labels == []


def test_create_for_classification__assigns_unique_file_id(fake):
    file1 = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name=f"{fake.word()}1.pdf",
        path=f"/path/{fake.word()}1.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    file2 = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name=f"{fake.word()}2.pdf",
        path=f"/path/{fake.word()}2.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    assert file1.id() != file2.id()


def test_create_for_classification__sets_processing_status(fake):
    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name="test.pdf",
        path="/path/test.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    assert file.state.status == Status.PROCESSING
    assert file.state.error_message is None


def test_create_for_classification__creates_labels_correctly(fake):
    labels = ["invoice", "financial", "urgent"]

    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name="test.pdf",
        path="/path/test.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=labels,
    )

    assert len(file.labels) == 3
    assert "invoice" in file.labels
    assert "financial" in file.labels
    assert "urgent" in file.labels


def test_create_for_classification__assigns_created_at_timestamp(fake):
    file = FileFactory.create_for_classification(
        tenant_id=fake.uuid4(),
        name="test.pdf",
        path="/path/test.pdf",
        group_id=fake.uuid4(),
        workflow_params={},
        labels=[],
    )

    assert file.created_at is not None
