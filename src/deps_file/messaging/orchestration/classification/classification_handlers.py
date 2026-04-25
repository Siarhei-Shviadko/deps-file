from ..shared import Error, ErrorType
from .classification_saga_data import ClassifySagaData
from .commands import ClassifyFileReply, CommandWithError

__all__ = ["FileClassificationHandlers"]


class FileClassificationHandlers:
    @staticmethod
    def evaluate_error_from_reply(data: ClassifySagaData, reply: CommandWithError) -> None:
        if reply.has_error:
            data.error = FileClassificationHandlers.build_error_from_reply(reply)

    @staticmethod
    def build_error_from_reply(reply: CommandWithError) -> Error:
        return Error(ErrorType(reply.error_type), reply.error_message)

    @staticmethod
    def evaluate_error(
        data: ClassifySagaData,
        error_type: ErrorType = ErrorType.SYSTEM,
        error_message: str = "",
    ) -> None:
        data.error = Error(type_=error_type, message=error_message)

    @staticmethod
    def evaluate_classification_result(data: ClassifySagaData, reply: ClassifyFileReply) -> None:
        FileClassificationHandlers.evaluate_error_from_reply(data, reply)
        if not reply.has_error:
            data.file_name = reply.document_name
            data.document_id = reply.document_id
            data.document_type_id = reply.document_type_id
