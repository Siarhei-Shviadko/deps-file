from uuid import uuid4

import pytest

from deps_file.domain.model.file.reference import Reference, ReferenceType
from tests.factories import FileReferenceFactory

__all__ = [
    "test_file_reference_1",
    "test_file_reference_2",
    "test_file_reference_document",
    "test_file_reference_batch",
    "test_file_reference_for_deletion",
    "test_file_references_multiple",
]


@pytest.fixture
def test_file_reference_1() -> Reference:
    return FileReferenceFactory.create_document_reference(
        entity_id=str(uuid4()),
        entity_name="Test Document 1",
    )


@pytest.fixture
def test_file_reference_2() -> Reference:
    return FileReferenceFactory.create_document_reference(
        entity_id=str(uuid4()),
        entity_name="Test Document 2",
    )


@pytest.fixture
def test_file_reference_document() -> Reference:
    return Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Document Reference",
    )


@pytest.fixture
def test_file_reference_batch() -> Reference:
    return Reference(
        entity_type=ReferenceType.BATCH,
        entity_id=str(uuid4()),
        entity_name="Batch Reference",
    )


@pytest.fixture
def test_file_reference_for_deletion() -> Reference:
    return FileReferenceFactory.create_document_reference()


@pytest.fixture
def test_file_references_multiple() -> list[Reference]:
    return [
        FileReferenceFactory.create_document_reference(
            entity_name="Multi Document 1",
        ),
        FileReferenceFactory.create_document_reference(
            entity_name="Multi Document 2",
        ),
        FileReferenceFactory.create_batch_reference(
            entity_name="Multi Batch 1",
        ),
    ]
