from typing import Any

from deps_message_flow.commands.consumer import (
    CommandWithDestination,
    CommandWithDestinationBuilder,
)
from deps_message_flow.sagas.orchestration import SagaData

from deps_file.domain.model import Status

from ..shared import Destination, Error, ErrorType
from .commands import PerformParsing, PerformUnification

__all__ = ["ProcessingSagaData"]


class ProcessingSagaData(SagaData):
    def __init__(
        self,
        file_id: str,
        tenant_id: str,
        files: list[str],
        parsing_features: list[str],
        engine: str | None = None,
        language: str | None = None,
        *,
        document_type_id: str | None = None,
        current_status: Status = Status.PROCESSING,
        error: Error | None = None,
    ) -> None:
        super().__init__(entity_id=file_id)

        self.file_id = file_id
        self.tenant_id = tenant_id
        self.files = files
        self.engine = engine
        self.language = language
        self.parsing_features = parsing_features

        self.document_type_id = document_type_id

        self.current_status = current_status
        self.error = error

    def is_invoke_next_step(self) -> bool:
        return self.error is None

    def is_local_step_failed(self) -> bool:
        return self.error is not None

    def perform_unification(self) -> CommandWithDestination:
        return (
            CommandWithDestinationBuilder.send(PerformUnification(self.file_id, self.files, None))
            .to(Destination.UNIFIER_SERVICE)
            .build()
        )

    def perform_unified_entity_parsing(self) -> CommandWithDestination:
        return (
            CommandWithDestinationBuilder.send(
                PerformParsing(
                    tenant_id=self.tenant_id,
                    document_id=self.file_id,
                    files=self.files,
                    engine=self.engine,
                    language=self.language,
                    features=self.parsing_features,
                ),
            )
            .to(Destination.PARSING_SERVICE)
            .build()
        )

    def set_error_state(self) -> None:
        if self.error is not None:
            self.current_status = Status.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "tenant_id": self.tenant_id,
            "files": self.files,
            "engine": self.engine,
            "language": self.language,
            "parsing_features": self.parsing_features,
            "document_type_id": self.document_type_id,
            "current_status": self.current_status.value,
            "error_type": self.error.type.value if self.error is not None else None,
            "error_message": self.error.message if self.error is not None else None,
        }

    @classmethod
    def from_dict(cls, raw_data: dict[str, Any]) -> "ProcessingSagaData":
        return cls(
            file_id=raw_data["file_id"],
            tenant_id=raw_data["tenant_id"],
            files=raw_data["files"],
            engine=raw_data["engine"],
            language=raw_data["language"],
            parsing_features=raw_data["parsing_features"],
            document_type_id=raw_data["document_type_id"],
            current_status=Status(raw_data["current_status"]),
            error=Error(ErrorType(raw_data["error_type"]), raw_data["error_message"])
            if raw_data["error_type"] is not None and raw_data["error_message"] is not None
            else None,
        )
