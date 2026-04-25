from typing import Any

from deps_message_flow.commands.consumer import (
    CommandWithDestination,
    CommandWithDestinationBuilder,
)
from deps_message_flow.sagas.orchestration import SagaData

from deps_file.constants import SPLIT_COMMANDS_CHANNEL

from ..shared import Error, ErrorType
from .commands import SplitFile

__all__ = ["SplitSagaData"]


class SplitSagaData(SagaData):  # noqa: WPS230
    def __init__(
        self,
        file_id: str,
        tenant_id: str,
        file_path: str,
        file_name: str,
        group_id: str,
        document_type_id: str,
        classification_enabled: bool,
        parsing_features: list[str] | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        needs_unifier: bool = False,
        needs_extraction: bool = True,
        assigned_to_me: bool = False,
        metadata: dict[str, Any] | None = None,
        *,
        batch_id: str | None = None,
        batch_name: str | None = None,
        error: Error | None = None,
    ) -> None:
        super().__init__(entity_id=file_id)

        self.file_id = file_id
        self.tenant_id = tenant_id
        self.file_path = file_path
        self.file_name = file_name
        self.group_id = group_id
        self.document_type_id = document_type_id
        self.classification_enabled = classification_enabled
        self.engine = engine
        self.language = language
        self.parsing_features = parsing_features
        self.llm_type = llm_type
        self.needs_unifier = needs_unifier
        self.needs_extraction = needs_extraction
        self.assigned_to_me = assigned_to_me
        self.metadata = metadata

        self.batch_id = batch_id
        self.batch_name = batch_name

        self.error = error

    def perform_splitting(self) -> CommandWithDestination:
        return (
            CommandWithDestinationBuilder.send(
                SplitFile(
                    file_id=self.file_id,
                    file_name=self.file_name,
                    group_id=self.group_id,
                    file_path=self.file_path,
                    document_type_id=self.document_type_id,
                    classification_enabled=self.classification_enabled,
                    parsing_features=self.parsing_features,
                    engine=self.engine,
                    language=self.language,
                    llm_type=self.llm_type,
                    needs_unifier=self.needs_unifier,
                    needs_extraction=self.needs_extraction,
                    assigned_to_me=self.assigned_to_me,
                    metadata=self.metadata,
                ),
            )
            .to(SPLIT_COMMANDS_CHANNEL)
            .build()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "tenant_id": self.tenant_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "group_id": self.group_id,
            "document_type_id": self.document_type_id,
            "classification_enabled": self.classification_enabled,
            "engine": self.engine,
            "language": self.language,
            "parsing_features": self.parsing_features,
            "llm_type": self.llm_type,
            "needs_unifier": self.needs_unifier,
            "needs_extraction": self.needs_extraction,
            "assigned_to_me": self.assigned_to_me,
            "metadata": self.metadata,
            "error_type": self.error.type.value if self.error is not None else None,
            "error_message": self.error.message if self.error is not None else None,
            "batch_id": self.batch_id,
            "batch_name": self.batch_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SplitSagaData":
        return cls(
            file_id=data["file_id"],
            tenant_id=data["tenant_id"],
            file_path=data["file_path"],
            file_name=data["file_name"],
            group_id=data["group_id"],
            document_type_id=data["document_type_id"],
            classification_enabled=data["classification_enabled"],
            parsing_features=data["parsing_features"],
            engine=data.get("engine"),
            language=data.get("language"),
            llm_type=data.get("llm_type"),
            needs_unifier=data.get("needs_unifier", False),
            needs_extraction=data.get("needs_extraction", True),
            assigned_to_me=data.get("assigned_to_me", False),
            metadata=data.get("metadata"),
            error=Error(ErrorType(data["error_type"]), data["error_message"])
            if data.get("error_type") is not None and data.get("error_message") is not None
            else None,
            batch_id=data.get("batch_id"),
            batch_name=data.get("batch_name"),
        )
