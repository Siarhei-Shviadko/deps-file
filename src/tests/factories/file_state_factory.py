import factory

from deps_file.domain.model.file.state import ErrorCode, State, Status


class StateFactory(factory.Factory):
    class Meta:
        model = State

    status = Status.PROCESSING
    error_message = None
    error_code = None

    @classmethod
    def processing(cls, **kwargs):
        return cls(status=Status.PROCESSING, **kwargs)

    @classmethod
    def completed(cls, **kwargs):
        return cls(status=Status.COMPLETED, **kwargs)

    @classmethod
    def failed(cls, error_message="Processing failed", error_code=ErrorCode.FAIL_PROCESSING, **kwargs):
        return cls(status=Status.FAILED, error_message=error_message, error_code=error_code, **kwargs)
