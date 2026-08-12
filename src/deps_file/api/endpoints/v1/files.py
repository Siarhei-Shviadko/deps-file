import json
import urllib
from datetime import datetime
from typing import Any, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)

from deps_file.api.auth import get_current_user_tenant
from deps_file.api.endpoint_marker import MarkerRoute
from deps_file.api.endpoint_visibility import Visibility
from deps_file.api.serializers.v1 import (
    BaseFileClassificationRequest,
    BaseFileSplittingRequest,
    BatchCreationRequest,
    BatchCreationResponse,
    DocumentCreationRequest,
    DocumentCreationResponse,
    FileClassificationRequest,
    FileListResponse,
    FileProcessRequest,
    FileResponse,
    FileResponseMapper,
    FileSplittingRequest,
    FileUploadResponse,
)
from deps_file.application import CommandFileService, QueryFileService
from deps_file.constants import DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from deps_file.containers import Containers
from deps_file.domain.exceptions import IllegalArgument
from deps_file.domain.model import FileSortBy, FileSortOrder

__all__ = ["files_router"]

files_router = APIRouter(prefix="/v1/files", tags=["Files"], route_class=MarkerRoute)


def decoded_file_name(name: str) -> str:
    return urllib.parse.unquote(name)


def parse_json_str(value: str | None, field_name: str) -> Any:
    if value is None or value == "":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise IllegalArgument(f"Invalid JSON in field '{field_name}'. {str(e)}")


@files_router.get(
    "",
    response_model=FileListResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def get_files(
    tenant_id: str = Depends(get_current_user_tenant),
    name: str | None = Query(default=None),
    state: list[str] | None = Query(default=None),
    labels: list[str] | None = Query(default=None),
    date_start: datetime | None = Query(default=None, alias="dateStart"),
    date_end: datetime | None = Query(default=None, alias="dateEnd"),
    reference_available: bool | None = Query(default=None, alias="referenceAvailable"),
    reference: str | None = Query(default=None),
    page: int = Query(default=DEFAULT_PAGE_NUMBER, ge=1),
    per_page: int = Query(default=DEFAULT_PAGE_SIZE, alias="perPage", ge=1, le=MAX_PAGE_SIZE),
    sort_by: FileSortBy = Query(default=FileSortBy.CREATED_AT, alias="sortBy"),
    sort_order: FileSortOrder = Query(default=FileSortOrder.DESC, alias="sortOrder"),
    query_file_service: QueryFileService = Depends(Provide[Containers.query_file_service]),
) -> FileListResponse:
    files_info = query_file_service.find_all_with(
        tenant_id=tenant_id,
        name=name,
        state=state,
        labels=labels,
        date_start=date_start,
        date_end=date_end,
        reference_available=reference_available,
        entity_name=reference,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return FileResponseMapper.to_file_list_response(files_info)


@files_router.get(
    "/{file_id}",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def get_file(
    file_id: str,
    tenant_id: str = Depends(get_current_user_tenant),
    query_file_service: QueryFileService = Depends(Provide[Containers.query_file_service]),
) -> FileResponse:
    file_info = query_file_service.find_file(file_id=file_id, tenant_id=tenant_id)

    return FileResponseMapper.to_file_response(file_info)


@files_router.get(
    "/{file_id}/content",
    status_code=status.HTTP_200_OK,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def get_file_content(
    file_id: str,
    tenant_id: str = Depends(get_current_user_tenant),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> Response:
    content, file_name = command_file_service.get_file_content(file_id=file_id, tenant_id=tenant_id)

    return FileResponseMapper.to_file_content_response(content=content, file_name=file_name)


@files_router.post(
    "/process",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
async def process_file(
    file: UploadFile = File(...),
    engine: str | None = Form(None),
    language: str | None = Form(None),
    llm_type: str | None = Form(None, validation_alias="llmType", alias="llmType"),
    parsing_features: Optional[str] = Form(
        None,
        alias="parsingFeatures",
        validation_alias="parsingFeatures",
        description=(
            r'Parsing features as JSON string. Swagger format: "[\\"text\\", \\"images\\"]". '
            'REST API format: ["text", "images"]'
        ),
    ),
    needs_unifier: bool = Form(..., validation_alias="needsUnifier", alias="needsUnifier"),
    needs_extraction: bool = Form(..., validation_alias="needsExtraction", alias="needsExtraction"),
    assigned_to_me: bool = Form(..., validation_alias="assignedToMe", alias="assignedToMe"),
    metadata: Optional[str] = Form(
        None,
        description=(
            r'Metadata as JSON string. Swagger format: "{\\"name\\": \\"test\\"}". REST API format: {"name": "test"}'
        ),
    ),
    labels: Optional[str] = Form(
        None,
        description=r'Labels as JSON string. Swagger format: "[\\"L1\\", \\"L2\\"]". REST API format: ["L1", "L2"]',
    ),
    tenant_id: str = Depends(get_current_user_tenant),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> FileUploadResponse:
    parsed_parsing_features = parse_json_str(parsing_features, "parsingFeatures")
    parsed_labels = parse_json_str(labels, "labels")
    parsed_metadata = parse_json_str(metadata, "metadata")

    file_process_request = FileProcessRequest(
        engine=engine,
        language=language,
        llm_type=llm_type,
        parsing_features=parsed_parsing_features,
        needs_unifier=needs_unifier,
        needs_extraction=needs_extraction,
        assigned_to_me=assigned_to_me,
        metadata=parsed_metadata,
        labels=parsed_labels,
    )
    processed_file = command_file_service.process(
        tenant_id=tenant_id,
        name=decoded_file_name(file.filename),
        content=await file.read(),
        workflow_params=file_process_request.workflow_params_to_dict(),
        labels=file_process_request.labels,
    )

    return FileUploadResponse.from_domain(processed_file)


@files_router.post(
    "/classify",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
async def classify_file(
    file: UploadFile = File(...),
    engine: str | None = Form(None),
    language: str | None = Form(None),
    llm_type: str | None = Form(None, validation_alias="llmType", alias="llmType"),
    parsing_features: Optional[str] = Form(
        None,
        alias="parsingFeatures",
        validation_alias="parsingFeatures",
        description=(
            r'Parsing features as JSON string. Swagger format: "[\\"text\\", \\"images\\"]". '
            'REST API format: ["text", "images"]'
        ),
    ),
    needs_unifier: bool = Form(..., validation_alias="needsUnifier", alias="needsUnifier"),
    needs_extraction: bool = Form(..., validation_alias="needsExtraction", alias="needsExtraction"),
    assigned_to_me: bool = Form(..., validation_alias="assignedToMe", alias="assignedToMe"),
    metadata: Optional[str] = Form(
        None,
        description=(
            r'Metadata as JSON string. Swagger format: "{\\"name\\": \\"test\\"}". REST API format: {"name": "test"}'
        ),
    ),
    labels: Optional[str] = Form(
        None,
        description=r'Labels as JSON string. Swagger format: "[\\"L1\\", \\"L2\\"]". REST API format: ["L1", "L2"]',
    ),
    group_id: str = Form(..., validation_alias="groupId", alias="groupId"),
    tenant_id: str = Depends(get_current_user_tenant),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> FileUploadResponse:
    parsed_parsing_features = parse_json_str(parsing_features, "parsingFeatures")
    parsed_labels = parse_json_str(labels, "labels")
    parsed_metadata = parse_json_str(metadata, "metadata")

    request_data = FileClassificationRequest(
        engine=engine,
        language=language,
        llm_type=llm_type,
        parsing_features=parsed_parsing_features,
        needs_unifier=needs_unifier,
        needs_extraction=needs_extraction,
        assigned_to_me=assigned_to_me,
        metadata=parsed_metadata,
        labels=parsed_labels,
        group_id=group_id,
    )

    classified_file = command_file_service.classify(
        tenant_id=tenant_id,
        name=decoded_file_name(file.filename),
        content=await file.read(),
        group_id=request_data.group_id,
        workflow_params=request_data.to_workflow_params_dict(),
        labels=request_data.normalized_labels,
    )

    return FileUploadResponse.from_domain(classified_file)


@files_router.patch(
    "/{fileId}/classify",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def classify_existing_file(
    file_id: str = Path(..., alias="fileId"),
    tenant_id: str = Depends(get_current_user_tenant),
    classify_file_request: BaseFileClassificationRequest = Body(...),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> None:
    command_file_service.classify_file(
        file_id=file_id,
        tenant_id=tenant_id,
        group_id=classify_file_request.group_id,
        workflow_params=classify_file_request.to_workflow_params_dict(),
    )


@files_router.post(
    "/split",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
async def split_file(
    file: UploadFile = File(...),
    document_type_id: str | None = Form(None, validation_alias="documentTypeId", alias="documentTypeId"),
    classification_enabled: bool = Form(..., validation_alias="classificationEnabled", alias="classificationEnabled"),
    engine: str | None = Form(None),
    language: str | None = Form(None),
    llm_type: str | None = Form(None, validation_alias="llmType", alias="llmType"),
    parsing_features: Optional[str] = Form(
        None,
        alias="parsingFeatures",
        validation_alias="parsingFeatures",
        description=(
            r'Parsing features as JSON string. Swagger format: "[\\"text\\", \\"images\\"]". '
            'REST API format: ["text", "images"]'
        ),
    ),
    needs_unifier: bool = Form(..., validation_alias="needsUnifier", alias="needsUnifier"),
    needs_extraction: bool = Form(..., validation_alias="needsExtraction", alias="needsExtraction"),
    assigned_to_me: bool = Form(..., validation_alias="assignedToMe", alias="assignedToMe"),
    needs_splitting_proposal_review: bool = Form(
        default=False,
        validation_alias="needsSplittingProposalReview",
        alias="needsSplittingProposalReview",
    ),
    metadata: Optional[str] = Form(
        None,
        description=(
            r'Metadata as JSON string. Swagger format: "{\\"name\\": \\"test\\"}". REST API format: {"name": "test"}'
        ),
    ),
    labels: Optional[str] = Form(
        None,
        description=r'Labels as JSON string. Swagger format: "[\\"L1\\", \\"L2\\"]". REST API format: ["L1", "L2"]',
    ),
    group_id: str = Form(..., validation_alias="groupId", alias="groupId"),
    tenant_id: str = Depends(get_current_user_tenant),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> FileUploadResponse:
    parsed_parsing_features = parse_json_str(parsing_features, "parsingFeatures")
    parsed_labels = parse_json_str(labels, "labels")
    parsed_metadata = parse_json_str(metadata, "metadata")

    request_data = FileSplittingRequest(
        document_type_id=document_type_id,
        classification_enabled=classification_enabled,
        engine=engine,
        language=language,
        llm_type=llm_type,
        parsing_features=parsed_parsing_features,
        needs_unifier=needs_unifier,
        needs_extraction=needs_extraction,
        assigned_to_me=assigned_to_me,
        needs_splitting_proposal_review=needs_splitting_proposal_review,
        metadata=parsed_metadata,
        labels=parsed_labels,
        group_id=group_id,
    )

    split_file_result = command_file_service.split(
        tenant_id=tenant_id,
        name=decoded_file_name(file.filename),
        content=await file.read(),
        group_id=request_data.group_id,
        classification_enabled=request_data.classification_enabled,
        workflow_params=request_data.to_workflow_params_dict(),
        labels=request_data.normalized_labels,
    )

    return FileUploadResponse.from_domain(split_file_result)


@files_router.patch(
    "/{fileId}/split",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def splitting_existing_file(
    file_id: str = Path(..., alias="fileId"),
    tenant_id: str = Depends(get_current_user_tenant),
    splitting_file_request: BaseFileSplittingRequest = Body(...),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> None:
    command_file_service.split_file(
        file_id=file_id,
        tenant_id=tenant_id,
        group_id=splitting_file_request.group_id,
        classification_enabled=splitting_file_request.classification_enabled,
        workflow_params=splitting_file_request.to_workflow_params_dict(),
    )


@files_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def delete_files(
    tenant_id: str = Depends(get_current_user_tenant),
    ids: set[str] = Query(...),
    command_file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> None:
    command_file_service.delete_files(ids=ids, tenant_id=tenant_id)


@files_router.post(
    "/{fileId}/create-document",
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def create_document_from_file(
    file_id: str = Path(..., alias="fileId"),
    data_request: DocumentCreationRequest = Body(...),
    tenant_id: str = Depends(get_current_user_tenant),
    file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> DocumentCreationResponse:
    document_id, document_name = file_service.create_document_from_file(
        file_id=file_id,
        tenant_id=tenant_id,
        document_type_id=data_request.document_type_id,
    )

    return DocumentCreationResponse(
        document_id=document_id,
        document_name=document_name,
    )


@files_router.post(
    "/{fileId}/create-batch",
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def create_batch_from_file(
    file_id: str = Path(..., alias="fileId"),
    data_request: BatchCreationRequest = Body(...),
    tenant_id: str = Depends(get_current_user_tenant),
    file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> BatchCreationResponse:
    return BatchCreationResponse(
        batch_id=file_service.create_batch_from_file(
            file_id=file_id,
            tenant_id=tenant_id,
            batch_name=data_request.batch_name,
            batch_files=data_request.batch_files,
            group_id=data_request.group_id,
        ),
    )


@files_router.post(
    "/{fileId}/restart",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
def restart_file(
    file_id: str = Path(..., alias="fileId"),
    tenant_id: str = Depends(get_current_user_tenant),
    file_service: CommandFileService = Depends(Provide[Containers.command_file_service]),
) -> None:
    file_service.restart_file(
        file_id=file_id,
        tenant_id=tenant_id,
    )
