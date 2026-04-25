import pytest

__all__ = ["classify_test_values", "splitting_test_values"]


@pytest.fixture
def classify_test_values():
    return {
        "tenant_id": "test_tenant_id",
        "file_name": "classify_file.pdf",
        "group_id": "test_group_id",
        "labels": ["label1", "label2"],
        "content": b"Classification content",
    }


@pytest.fixture
def splitting_test_values():
    return {
        "tenant_id": "test_tenant_id",
        "file_name": "splitting_file.pdf",
        "document_type_id": "test_document_type_id",
        "group_id": "test_group_id",
        "labels": ["label1", "label2"],
        "content": b"Splitting content",
    }
