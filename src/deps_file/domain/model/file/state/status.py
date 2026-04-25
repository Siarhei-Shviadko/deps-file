from ...shared import ExtendedEnum

__all__ = ["Status"]


class Status(ExtendedEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
