import logging
from typing import TYPE_CHECKING

from deps_message_flow.sagas.orchestration_simple_dsl import SimpleSaga

from ..shared import SagaFailed, SagaRolledBack
from .commands import PerformParsingReply, PerformUnificationReply
from .processing_handlers import ProcessingHandlers as Handlers
from .processing_saga_data import ProcessingSagaData as SagaData

if TYPE_CHECKING:
    from deps_file.application.file import CommandFileService

__all__ = ["ProcessingSaga"]


class ProcessingSaga(SimpleSaga[SagaData]):
    def __init__(self, command_file_service: "CommandFileService") -> None:
        self._command_file_service = command_file_service
        self._saga_definition = (
            # Unification
            self.step()
            .invoke_participant(
                SagaData.perform_unification,
            )
            .on_reply(PerformUnificationReply, Handlers.evaluate_error_from_reply)
            # Parsing
            .step()
            .invoke_participant(
                SagaData.perform_unified_entity_parsing,
                predicate=SagaData.is_invoke_next_step,
            )
            .on_reply(PerformParsingReply, Handlers.evaluate_error_from_reply)
            # Set error state
            .step()
            .invoke_local(SagaData.set_error_state)
            .build()
        )

        self._logger = logging.getLogger(self.__class__.__name__)

    def on_saga_completed_successfully(self, saga_id: str, data: SagaData) -> None:
        self._logger.info(
            "Processing File Saga for file `%s` completed successfully",
            data.file_id,
        )

        if data.error is None:
            self._command_file_service.complete_processing(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
            )
        else:
            self._command_file_service.fail_processing(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
                error_message=data.error.message,
            )

    def on_saga_rolled_back(self, saga_id: str, data: SagaData) -> None:
        self._logger.warning(
            "Saga: %s for file %s processing is rolled back",
            saga_id,
            data.file_id,
        )

        raise SagaRolledBack("File processing saga failed and rolled back")

    def on_saga_failed(self, saga_id: str, data: SagaData) -> None:
        self._logger.error(
            "Saga: %s for file %s processing is failed",
            saga_id,
            data.file_id,
            exc_info=True,
        )

        raise SagaFailed("File processing saga failed")
