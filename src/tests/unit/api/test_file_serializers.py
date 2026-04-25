import pytest
from pydantic import ValidationError

from deps_file.api.serializers.v1 import (
    DocumentCreationRequest,
    FileClassificationRequest,
    FileSplittingRequest,
)
from deps_file.domain.model.file.file import File
from deps_file.domain.model.file.file_factory import FileFactory


def test_file_classification_request__validates_required_fields():
    with pytest.raises(ValidationError) as exc_info:
        FileClassificationRequest()

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("groupId",) for error in errors)


def test_file_classification_request__normalizes_labels():
    request = FileClassificationRequest(
        groupId="test-group",
        labels=["invoice,financial", "urgent"],
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
    )

    normalized = FileClassificationRequest.normalize_str_list(request.labels)
    assert "invoice" in normalized
    assert "financial" in normalized
    assert "urgent" in normalized
    assert len(normalized) == 3


def test_file_classification_request__handles_empty_labels():
    request = FileClassificationRequest(
        groupId="test-group",
        labels=None,
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
    )
    normalized = FileClassificationRequest.normalize_str_list(request.labels)
    assert normalized == []


def test_file_classification_request__converts_to_workflow_params():
    request = FileClassificationRequest(
        groupId="test-group",
        engine="advanced",
        language="en",
        llmType="gpt-4",
        parsingFeatures=["table", "text"],
        needsUnifier=True,
        needsExtraction=False,
        assignedToMe=True,
        metadata={"priority": "high"},
    )

    workflow_params = request.to_workflow_params_dict()

    assert workflow_params["engine"] == "advanced"
    assert workflow_params["language"] == "en"
    assert workflow_params["llm_type"] == "gpt-4"
    assert workflow_params["parsing_features"] == ["table", "text"]
    assert workflow_params["needs_unifier"] is True
    assert workflow_params["needs_extraction"] is False
    assert workflow_params["assigned_to_me"] is True
    assert workflow_params["metadata"] == {"priority": "high"}


def test_file_classification_request__handles_defaults():
    request = FileClassificationRequest(
        groupId="test-group",
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
    )

    workflow_params = request.to_workflow_params_dict()

    assert workflow_params["metadata"] == {}
    assert workflow_params["parsing_features"] == []


@pytest.mark.parametrize(
    "parsing_features,expected",
    [
        (["table,text", "images"], ["table", "text", "images"]),
        (["table", "text,images"], ["table", "text", "images"]),
        (["table, text, images"], ["table", "text", "images"]),
        ([], []),
        (None, []),
    ],
)
def test_normalize_str_list__handles_various_formats(parsing_features, expected):
    result = FileClassificationRequest.normalize_str_list(parsing_features)
    assert result == expected


def test_file_classification_request__alias_mapping():
    data = {
        "groupId": "test-group",
        "llmType": "gpt-4",
        "parsingFeatures": ["table"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    request = FileClassificationRequest(**data)

    assert request.group_id == "test-group"
    assert request.llm_type == "gpt-4"
    assert request.parsing_features == ["table"]
    assert request.needs_unifier is True
    assert request.needs_extraction is False
    assert request.assigned_to_me is True


def test_file_splitting_request__validates_required_fields():
    with pytest.raises(ValidationError) as exc_info:
        FileSplittingRequest()

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("groupId",) for error in errors)


def test_file_splitting_request__normalizes_labels():
    request = FileSplittingRequest(
        groupId="test-group",
        classification_enabled=False,
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
        labels=["label1, label2", "label3"],
    )

    assert request.normalized_labels == ["label1", "label2", "label3"]


def test_file_splitting_request__handles_empty_labels():
    request = FileSplittingRequest(
        groupId="test-group",
        classification_enabled=False,
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
        labels=None,
    )

    assert request.normalized_labels == []


def test_file_splitting_request__converts_to_workflow_params():
    request = FileSplittingRequest(
        groupId="test-group",
        documentTypeId="test-doc-type",
        classificationEnabled=True,
        engine="advanced",
        language="en",
        llmType="gpt-4",
        parsingFeatures=["table", "text"],
        needsUnifier=True,
        needsExtraction=False,
        assignedToMe=True,
        metadata={"priority": "high"},
    )

    workflow_params = request.to_workflow_params_dict()

    assert workflow_params["document_type_id"] == "test-doc-type"
    assert workflow_params["engine"] == "advanced"
    assert workflow_params["language"] == "en"
    assert workflow_params["llm_type"] == "gpt-4"
    assert workflow_params["parsing_features"] == ["table", "text"]
    assert workflow_params["needs_unifier"] is True
    assert workflow_params["needs_extraction"] is False
    assert workflow_params["assigned_to_me"] is True
    assert workflow_params["metadata"] == {"priority": "high"}


def test_file_splitting_request__handles_defaults():
    request = FileSplittingRequest(
        groupId="test-group",
        classification_enabled=False,
        needsUnifier=False,
        needsExtraction=False,
        assignedToMe=False,
    )

    workflow_params = request.to_workflow_params_dict()

    assert workflow_params["metadata"] == {}
    assert workflow_params["parsing_features"] == []


@pytest.mark.parametrize(
    "parsing_features,expected",
    [
        (["table,text", "images"], ["table", "text", "images"]),
        (["table", "text,images"], ["table", "text", "images"]),
        (["table, text, images"], ["table", "text", "images"]),
        ([], []),
        (None, []),
    ],
)
def test_file_splitting_request__normalize_str_list__handles_various_formats(parsing_features, expected):
    result = FileSplittingRequest.normalize_str_list(parsing_features)
    assert result == expected


def test_file_splitting_request__alias_mapping():
    data = {
        "groupId": "test-group",
        "classificationEnabled": False,
        "llmType": "gpt-4",
        "parsingFeatures": ["table"],
        "needsUnifier": True,
        "needsExtraction": False,
        "assignedToMe": True,
    }

    request = FileSplittingRequest(**data)

    assert request.group_id == "test-group"
    assert request.classification_enabled == False
    assert request.llm_type == "gpt-4"
    assert request.parsing_features == ["table"]
    assert request.needs_unifier is True
    assert request.needs_extraction is False
    assert request.assigned_to_me is True


def test_document_creation_request__validates_required_fields():
    with pytest.raises(ValidationError) as exc_info:
        DocumentCreationRequest()

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("documentTypeId",) for error in errors)


def test_document_creation_request__accepts_valid_data():
    document_type_id = "test-doc-type-id"
    request = DocumentCreationRequest(documentTypeId=document_type_id)

    assert request.document_type_id == document_type_id


def test_document_creation_request__alias_mapping():
    data = {"documentTypeId": "test-doc-type-id"}

    request = DocumentCreationRequest(**data)

    assert request.document_type_id == "test-doc-type-id"
