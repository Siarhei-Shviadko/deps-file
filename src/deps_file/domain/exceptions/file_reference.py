from .base import AlreadyExistsError

__all__ = ["FileReferenceAlreadyExists"]


class FileReferenceAlreadyExists(AlreadyExistsError):
    code = "file_reference_already_exists"

    def __init__(self, file_id: str) -> None:
        super().__init__(f"File reference for file `{file_id}` already exists.")
