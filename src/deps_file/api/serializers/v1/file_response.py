from datetime import datetime
from typing import Any

from pydantic import Field

from deps_file.api.serializers import BaseSerializer
from deps_file.domain.model import File

from .file_reference_info import FileReferenceInfoResponse

__all__ = [
    "FileStateResponse",
    "WorkflowParamsResponse",
    "ProcessingParamsResponse",
    "FileResponse",
    "FileUploadResponse",
    "DocumentCreationResponse",
]


class FileStateResponse(BaseSerializer):
    status: str
    error_message: str | None = Field(None, alias="errorMessage")
    error_code: str | None = Field(None, alias="errorCode")


class WorkflowParamsResponse(BaseSerializer):
    document_type_id: str | None = Field(None, alias="documentTypeId")
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = Field(None, alias="llmType")
    parsing_features: list[str] = Field(alias="parsingFeatures")
    needs_unifier: bool = Field(..., alias="needsUnifier")
    needs_extraction: bool = Field(..., alias="needsExtraction")
    assigned_to_me: bool = Field(..., alias="assignedToMe")
    metadata: dict[str, Any] | None


class ProcessingParamsResponse(BaseSerializer):
    group_id: str | None = Field(None, alias="groupId")
    splitting_enabled: bool = Field(..., alias="splittingEnabled")
    classification_enabled: bool = Field(..., alias="classificationEnabled")
    workflow_params: WorkflowParamsResponse = Field(..., alias="workflowParams")


class FileResponse(BaseSerializer):
    id: str
    tenant_id: str = Field(..., alias="tenantId")
    name: str
    path: str
    state: FileStateResponse
    processing_params: ProcessingParamsResponse = Field(alias="processingParams")
    labels: list[str] | None = None
    reference: FileReferenceInfoResponse | None = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")


class FileUploadResponse(BaseSerializer):
    id: str

    @classmethod
    def from_domain(cls, file: File):
        return cls(id=file.id())


class DocumentCreationResponse(BaseSerializer):
    document_id: str = Field(..., alias="documentId")
    document_name: str = Field(..., alias="documentName")
