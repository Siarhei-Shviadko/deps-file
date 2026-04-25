from ..shared import Error, ErrorType
from .commands import SplitFileReply
from .splitting_saga_data import SplitSagaData

__all__ = ["FileSplittingHandlers"]


class FileSplittingHandlers:
    @staticmethod
    def evaluate_splitting_result(data: SplitSagaData, reply: SplitFileReply) -> None:
        if reply.has_error:
            data.error = Error(ErrorType(reply.error_type), reply.error_message)
        else:
            data.batch_id = reply.batch_id
            data.batch_name = reply.batch_name
