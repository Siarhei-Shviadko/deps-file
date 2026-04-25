from deps_file.domain.exceptions import RestClientError

__all__ = ["GroupProxyRequestError", "FileStorageRequestError", "DocumentProxyRequestError", "BatchProxyRequestError"]


class GroupProxyRequestError(RestClientError):
    pass


class FileStorageRequestError(Exception):
    pass


class DocumentProxyRequestError(RestClientError):
    pass


class BatchProxyRequestError(RestClientError):
    pass
