from datetime import datetime, timezone

from ...exceptions import FileIsNotFailed, FileReferenceAlreadyExists
from ..shared import Event, Guard, ImmutableCheck, LengthCheck, TenantId
from .constants import MAX_FILE_NAME_LENGTH, MAX_FILE_PATH_LENGTH
from .events import FileDeleted, FileProcessed, FileStateUpdated, Purpose
from .file_id import FileId
from .processing_params import ProcessingParams, WorkflowParamsDict
from .reference import Reference, ReferenceType
from .state import ErrorCode, State, Status

__all__ = ["File"]


class File:
    id = Guard[FileId](FileId, ImmutableCheck())
    tenant_id = Guard[TenantId](TenantId, ImmutableCheck())
    name = Guard[str](str, LengthCheck(max_length=MAX_FILE_NAME_LENGTH))
    path = Guard[str](str, LengthCheck(max_length=MAX_FILE_PATH_LENGTH))
    processing_params = Guard[ProcessingParams](ProcessingParams)
    state = Guard[State](State)
    labels = Guard[list[str]](list, ImmutableCheck())
    reference: Reference | None = None
    created_at = Guard[datetime](datetime, ImmutableCheck())
    updated_at = Guard[datetime](datetime)

    def __init__(
        self,
        tenant_id: str,
        name: str,
        path: str,
        processing_params: ProcessingParams,
        labels: list[str] | None = None,
        reference: Reference | None = None,
        id_: str | None = None,
        state: State = State(Status.PROCESSING),
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        *,
        events: list[Event] | None = None,
    ) -> None:
        self.id = FileId(id_) if id_ is not None else FileId()
        self.tenant_id = TenantId(tenant_id)
        self.name = name
        self.path = path
        self.state = state
        self.processing_params = processing_params
        self.created_at = created_at or datetime.now(timezone.utc)
        self.events = events or []
        self.commands: list = []

        if updated_at:
            self.updated_at = updated_at
        if labels is not None:
            self.labels = labels
        if reference is not None:
            self.reference = reference

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __repr__(self) -> str:
        return (
            f"<class '{self.__class__.__name__}': "
            f"{self.id=},"
            f"{self.tenant_id=},"
            f"{self.name=},"
            f"{self.path=},"
            f"{self.state=},"
            f"{self.processing_params=},"
            f"{self.labels=},"
            f"{self.reference=},"
            f"{self.created_at=},"
            f"{self.updated_at=}>"  # noqa: C812
        )

    @property
    def status(self) -> Status:
        return self.state.status

    def generate_pipeline_command(self) -> None:
        command = self.processing_params.generate_command()

        if hasattr(command, "file_id"):
            command.file_id = self.id()
        if hasattr(command, "file_name"):
            command.file_name = self.name
        if hasattr(command, "path"):
            command.path = self.path
        if hasattr(command, "files"):
            command.files = [self.path]
        if hasattr(command, "tenant_id"):
            command.tenant_id = self.tenant_id()

        self.commands.append(command)

    def classify(self, group_id: str, workflow_params: WorkflowParamsDict):
        self.check_reference_existence()
        self._update_processing_params(group_id, workflow_params, classification_enabled=True)
        self.generate_pipeline_command()

    def split(self, group_id: str, classification_enabled: bool, workflow_params: WorkflowParamsDict):
        self.check_reference_existence()
        self._update_processing_params(
            group_id=group_id,
            workflow_params=workflow_params,
            classification_enabled=classification_enabled,
            splitting_enabled=True,
        )
        self.generate_pipeline_command()

    def restart(self) -> None:
        if self.is_failed():
            self.generate_pipeline_command()
            self._set_processing_state()
        else:
            raise FileIsNotFailed(str(self.id.value))

    def complete_processing(self) -> None:
        self._set_completed_state()
        self._add_file_processed_event(Purpose.PROCESSING)

    def fail_processing(self, error_message: str) -> None:
        self._set_failed_state(error_message, ErrorCode.FAIL_PROCESSING)
        self._add_file_processed_event(Purpose.PROCESSING)

    def complete_classification(self, entity_id: str, entity_name: str) -> None:
        self.add_document_reference(entity_id, entity_name)
        self._set_completed_state()

    def fail_classification(self, error_message: str) -> None:
        self._set_failed_state(error_message, ErrorCode.FAIL_CLASSIFICATION)
        self._add_file_processed_event(Purpose.CLASSIFICATION)

    def complete_splitting(self, entity_id: str, entity_name: str) -> None:
        self.add_batch_reference(entity_id, entity_name)
        self._set_completed_state()

    def fail_splitting(self, error_message: str) -> None:
        self._set_failed_state(error_message, ErrorCode.FAIL_SPLITTING)
        self._add_file_processed_event(Purpose.SPLITTING)

    def add_document_reference(self, entity_id: str, entity_name: str):
        self._add_reference(ReferenceType.DOCUMENT, entity_id, entity_name)

    def add_batch_reference(self, entity_id: str, entity_name: str):
        self._add_reference(ReferenceType.BATCH, entity_id, entity_name)

    def check_reference_existence(self) -> None:
        if self.reference is not None:
            raise FileReferenceAlreadyExists(str(self.id.value))

    def is_failed(self) -> bool:
        return self.state.status == Status.FAILED

    def delete(self) -> None:
        self.events.append(FileDeleted(id=self.id(), path=self.path))

    def _update_processing_params(
        self,
        group_id: str,
        workflow_params: WorkflowParamsDict,
        classification_enabled: bool | None = None,
        splitting_enabled: bool | None = None,
    ) -> None:
        self.processing_params = ProcessingParams(
            group_id=group_id,
            splitting_enabled=splitting_enabled
            if splitting_enabled is not None
            else self.processing_params.splitting_enabled,
            classification_enabled=classification_enabled
            if classification_enabled is not None
            else self.processing_params.classification_enabled,
            workflow_params=workflow_params,
        )

    def _add_file_state_updated_event(self, error_message: str | None = None) -> None:
        self.events.append(
            FileStateUpdated(
                file_id=self.id(),
                state=self.status.value,
                metadata=self.processing_params.metadata,
                error_message=error_message,
            ),
        )

    def _add_file_processed_event(self, purpose: Purpose) -> None:
        self.events.append(
            FileProcessed(
                id=self.id(),
                status=self.status.value,
                purpose=purpose.value,
                metadata=self.processing_params.metadata,
                error_message=self.state.error_message,
            ),
        )

    def _add_reference(self, entity_type: ReferenceType, entity_id: str, entity_name: str) -> None:
        self.check_reference_existence()
        self._set_reference(entity_type, entity_id, entity_name)

    def _set_reference(self, entity_type: ReferenceType, entity_id: str, entity_name: str) -> None:
        self.reference = Reference(entity_type=entity_type, entity_id=entity_id, entity_name=entity_name)

    def _set_completed_state(self) -> None:
        self.state = State(Status.COMPLETED)
        self._add_file_state_updated_event()

    def _set_processing_state(self) -> None:
        self.state = State(Status.PROCESSING)
        self._add_file_state_updated_event()

    def _set_failed_state(self, error_message: str, error_code: ErrorCode) -> None:
        self.state = State(status=Status.FAILED, error_message=error_message, error_code=error_code)
        self._add_file_state_updated_event(error_message)
