from uuid import uuid4

import pytest

from deps_file.domain.exceptions import IllegalArgument
from deps_file.domain.model.file.reference import Reference, ReferenceType
from tests.factories import FileReferenceFactory


def test_create__with_complete_data__created():
    entity_id = str(uuid4())
    entity_name = "Test Document"

    reference = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )

    assert reference.entity_type == ReferenceType.DOCUMENT
    assert reference.entity_id == entity_id
    assert reference.entity_name == entity_name


def test_create__document_type__stored_correctly():
    reference = FileReferenceFactory.create_document_reference()

    assert reference.entity_type == ReferenceType.DOCUMENT


def test_create__batch_type__stored_correctly():
    reference = FileReferenceFactory.create_batch_reference()

    assert reference.entity_type == ReferenceType.BATCH


def test_equality__same_values__equal():
    entity_id = str(uuid4())
    entity_name = "Test Doc"
    reference_1 = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )
    reference_2 = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name=entity_name,
    )

    assert reference_1 == reference_2


def test_equality__different_values__not_equal():
    reference_1 = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Doc 1",
    )
    reference_2 = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=str(uuid4()),
        entity_name="Doc 2",
    )

    assert reference_1 != reference_2


def test_equality__comparing_with_non_file_reference__not_equal():
    reference = FileReferenceFactory.create_document_reference()

    assert reference != "not a file reference"
    assert reference != 123
    assert reference != None


def test_repr__returns_string_representation():
    entity_id = str(uuid4())
    reference = Reference(
        entity_type=ReferenceType.DOCUMENT,
        entity_id=entity_id,
        entity_name="Test Doc",
    )

    result = repr(reference)

    assert "ReferenceType.DOCUMENT" in result
    assert entity_id in result
    assert "Test Doc" in result


def test_immutability__cannot_change_entity_type():
    reference = FileReferenceFactory.create_document_reference()

    with pytest.raises(IllegalArgument):
        reference.entity_type = ReferenceType.BATCH


def test_immutability__cannot_change_entity_id():
    reference = FileReferenceFactory.create_document_reference()

    with pytest.raises(IllegalArgument):
        reference.entity_id = str(uuid4())


def test_immutability__cannot_change_entity_name():
    reference = FileReferenceFactory.create_document_reference()

    with pytest.raises(IllegalArgument):
        reference.entity_name = "New Name"
