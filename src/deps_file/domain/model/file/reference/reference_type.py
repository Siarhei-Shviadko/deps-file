from enum import Enum

__all__ = ["ReferenceType"]


class ReferenceType(str, Enum):
    DOCUMENT = "document"
    BATCH = "batch"
