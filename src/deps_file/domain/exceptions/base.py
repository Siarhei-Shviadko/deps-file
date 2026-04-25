__all__ = [
    "FileException",
    "NotFoundError",
    "IllegalArgument",
    "BusinessException",
    "RestClientError",
    "AlreadyExistsError",
]


class FileException(Exception):
    code = "file_exception"


class BusinessException(FileException):
    code = "business_exception"


class NotFoundError(BusinessException):
    code = "not_found_error"


class AlreadyExistsError(BusinessException):
    code = "already_exists_error"


class IllegalArgument(FileException):
    code = "illegal_argument"


class RestClientError(FileException):
    code = "rest_client_error"
