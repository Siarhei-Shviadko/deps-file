from ...shared import ExtendedEnum

__all__ = ["ErrorCode"]


class ErrorCode(ExtendedEnum):
    FAIL_PROCESSING = "error_during_processing"
    FAIL_CLASSIFICATION = "error_during_classification"
    FAIL_SPLITTING = "error_during_splitting"
