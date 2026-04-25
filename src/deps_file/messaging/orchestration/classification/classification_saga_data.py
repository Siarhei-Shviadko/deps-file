import logging
from typing import Any

from deps_message_flow.commands.consumer import (
    CommandWithDestination,
    CommandWithDestinationBuilder,
)
from deps_message_flow.sagas.orchestration import SagaData

from deps_file.constants import CLASSIFICATION_COMMANDS_CHANNEL
from deps_file.domain.model import Status

from ..shared import Destination, Error, ErrorType
from .commands import ClassifyFile

__all__ = ["ClassifySagaData"]


class ClassifySagaData(SagaData):  # noqa: WPS230
    def __init__(
        self,
        file_id: str,
        tenant_id: str,
        file_path: str,
        file_name: str,
        group_id: str,
        parsing_features: list[str],
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        needs_unifier: bool = False,
        needs_extraction: bool = False,
        assigned_to_me: bool = False,
        metadata: dict[str, Any] | None = None,
        *,
        document_id: str | None = None,
        document_name: str | None = None,
        document_type_id: str | None = None,
        current_status: Status = Status.PROCESSING,
        error: Error | None = None,
    ) -> None:
        super().__init__(entity_id=file_id)

        self.file_id = file_id
        self.tenant_id = tenant_id
        self.file_path = file_path
        self.file_name = file_name
        self.group_id = group_id
        self.engine = engine
        self.language = language
        self.parsing_features = parsing_features
        self.llm_type = llm_type
        self.needs_unifier = needs_unifier
        self.needs_extraction = needs_extraction
        self.assigned_to_me = assigned_to_me
        self.metadata = metadata

        self.document_id = document_id
        self.document_name = document_name
        self.document_type_id = document_type_id

        self.current_status = current_status
        self.error = error

    def is_invoke_next_step(self) -> bool:
        return self.error is None

    def is_local_step_failed(self) -> bool:
        return self.error is not None

    def perform_classification(self) -> CommandWithDestination:
        return (
            CommandWithDestinationBuilder.send(
                ClassifyFile(
                    file_id=self.file_id,
                    file_name=self.file_name,
                    group_id=self.group_id,
                    file_path=self.file_path,
                    parsing_features=self.parsing_features,
                    engine=self.engine,
                    language=self.language,
                    llm_type=self.llm_type,
                    needs_unifier=self.needs_unifier,
                    needs_extraction=self.needs_extraction,
                    assigned_to_me=self.assigned_to_me,
                    metadata=self.metadata,
                    start_processing=True,
                ),
            )
            .to(CLASSIFICATION_COMMANDS_CHANNEL)
            .build()
        )

    def set_error_state(self) -> None:
        if self.error is not None:
            self.current_status = Status.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "tenant_id": self.tenant_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "group_id": self.group_id,
            "engine": self.engine,
            "language": self.language,
            "parsing_features": self.parsing_features,
            "llm_type": self.llm_type,
            "metadata": self.metadata,
            "document_id": self.document_id,
            "document_type_id": self.document_type_id,
            "current_status": self.current_status.value,
            "error_type": self.error.type.value if self.error is not None else None,
            "error_message": self.error.message if self.error is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassifySagaData":
        return cls(
            file_id=data["file_id"],
            tenant_id=data["tenant_id"],
            file_path=data["file_path"],
            file_name=data["file_name"],
            group_id=data["group_id"],
            parsing_features=data["parsing_features"],
            engine=data.get("engine"),
            language=data.get("language"),
            llm_type=data.get("llm_type"),
            metadata=data.get("metadata"),
            document_id=data.get("document_id"),
            document_type_id=data.get("document_type_id"),
            current_status=Status(data["current_status"]),
            error=Error(ErrorType(data["error_type"]), data["error_message"])
            if data["error_type"] is not None and data["error_message"] is not None
            else None,
        )
