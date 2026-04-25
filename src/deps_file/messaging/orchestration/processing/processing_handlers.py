from ..shared import Error, ErrorType
from .commands import CommandWithError
from .processing_saga_data import ProcessingSagaData

__all__ = ["ProcessingHandlers"]


class ProcessingHandlers:
    @staticmethod
    def evaluate_error_from_reply(data: ProcessingSagaData, reply: CommandWithError) -> None:
        if reply.has_error:
            data.error = ProcessingHandlers.build_error_from_reply(reply)

    @staticmethod
    def build_error_from_reply(reply: CommandWithError) -> Error:
        return Error(ErrorType(reply.error_type), reply.error_message)

    @staticmethod
    def evaluate_error(
        data: ProcessingSagaData,
        error_type: ErrorType = ErrorType.SYSTEM,
        error_message: str = "",
    ) -> None:
        data.error = Error(type_=error_type, message=error_message)
