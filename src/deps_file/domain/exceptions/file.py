from .base import BusinessException, NotFoundError

__all__ = ["FileNotFound", "GroupNotFound", "FileIsNotFailed"]


class FileNotFound(NotFoundError):
    code = "file_not_found"

    def __init__(self, file_id: str) -> None:
        super().__init__(f"File with id `{file_id}` not found.")


class GroupNotFound(NotFoundError):
    code = "group_not_found"

    def __init__(self, group_id: str) -> None:
        super().__init__(f"Group with id `{group_id}` not found.")


class FileIsNotFailed(BusinessException):
    code = "file_is_not_failed"

    def __init__(self, file_id: str) -> None:
        super().__init__(f"File with id `{file_id}` is not failed.")
