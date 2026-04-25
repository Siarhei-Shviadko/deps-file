import logging
from typing import TYPE_CHECKING

from deps_message_flow.sagas.orchestration_simple_dsl import SimpleSaga

from ..shared import SagaFailed, SagaRolledBack
from .classification_handlers import FileClassificationHandlers as Handlers
from .classification_saga_data import ClassifySagaData as SagaData
from .commands import ClassifyFileReply

if TYPE_CHECKING:
    from deps_file.application.file import CommandFileService

__all__ = ["ClassifySaga"]


class ClassifySaga(SimpleSaga[SagaData]):
    def __init__(self, command_file_service: "CommandFileService") -> None:
        self._command_file_service = command_file_service
        self._saga_definition = (
            # Classification
            self.step()
            .invoke_participant(
                SagaData.perform_classification,
            )
            .on_reply(ClassifyFileReply, Handlers.evaluate_classification_result)
            # Set error state
            .step()
            .invoke_local(SagaData.set_error_state)
            .build()
        )

        self._logger = logging.getLogger(self.__class__.__name__)

    def on_saga_completed_successfully(self, saga_id: str, data: SagaData) -> None:
        self._logger.info(
            "File classification Saga for file `%s` completed successfully",
            data.file_id,
        )

        if data.error is None:
            self._logger.info(f"Saga: {saga_id} - completing classification for file {data.file_id}")
            self._command_file_service.complete_classification(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
                document_id=data.document_id,
                document_name=data.file_name,
                document_type_id=data.document_type_id,
            )
        else:
            self._logger.info(f"Saga: {saga_id} - failing classification for file {data.file_id}")
            self._logger.error(data.error)
            self._command_file_service.fail_classification(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
                error_message=data.error.message,
            )

    def on_saga_rolled_back(self, saga_id: str, data: SagaData) -> None:
        self._logger.warning(
            "Saga: %s for file %s classification is rolled back",
            saga_id,
            data.file_id,
        )

        raise SagaRolledBack("File classification saga failed and rolled back")

    def on_saga_failed(self, saga_id: str, data: SagaData) -> None:
        self._logger.error(
            "Saga: %s for file %s classification is failed",
            saga_id,
            data.file_id,
            exc_info=True,
        )

        raise SagaFailed("File classification saga failed")
