from ...shared import ExtendedEnum

__all__ = ["Purpose"]


class Purpose(ExtendedEnum):
    PROCESSING = "processing"
    CLASSIFICATION = "classification"
    SPLITTING = "splitting"
