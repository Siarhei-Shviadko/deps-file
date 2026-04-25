import logging
from typing import TYPE_CHECKING

from deps_message_flow.sagas.orchestration_simple_dsl import SimpleSaga

from .commands import SplitFileReply
from .splitting_handlers import FileSplittingHandlers
from .splitting_saga_data import SplitSagaData

if TYPE_CHECKING:
    from deps_file.application.file import CommandFileService

__all__ = ["SplitSaga"]


class SplitSaga(SimpleSaga[SplitSagaData]):
    def __init__(self, command_file_service: "CommandFileService") -> None:
        self._command_file_service = command_file_service
        self._saga_definition = (
            self.step()
            .invoke_participant(SplitSagaData.perform_splitting)
            .on_reply(SplitFileReply, FileSplittingHandlers.evaluate_splitting_result)
            .build()
        )

        self._logger = logging.getLogger(self.__class__.__name__)

    def on_saga_completed_successfully(self, saga_id: str, data: SplitSagaData) -> None:
        self._logger.info("File splitting Saga for file `%s` completed successfully", data.file_id)

        if data.error is None:
            self._logger.info(f"Saga: {saga_id} - completing splitting for file {data.file_id}")
            self._command_file_service.complete_splitting(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
                batch_id=data.batch_id,
                batch_name=data.batch_name,
            )
        else:
            self._logger.info(f"Saga: {saga_id} - failing splitting for file {data.file_id}")
            self._logger.error(data.error)
            self._command_file_service.fail_splitting(
                file_id=data.file_id,
                tenant_id=data.tenant_id,
                error_message=data.error.message,
            )

    def on_saga_rolled_back(self, saga_id: str, data: SplitSagaData) -> None:
        self._logger.warning("Saga: %s for file %s splitting is rolled back", saga_id, data.file_id)

    def on_saga_failed(self, saga_id: str, data: SplitSagaData) -> None:
        self._logger.error("Saga: %s for file %s splitting is failed", saga_id, data.file_id, exc_info=True)
