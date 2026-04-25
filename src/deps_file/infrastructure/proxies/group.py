import logging

from deps_file.application.group import IGroupProxy

from .exceptions import GroupProxyRequestError
from .generic import GenericProxy

__all__ = ["InternalGroupProxy"]


class InternalGroupProxy(IGroupProxy, GenericProxy):
    url_suffix = "/api-internal"
    exception = GroupProxyRequestError

    def __init__(
        self,
        base_url: str,
        timeout: int = 60,
        ssl_verify: bool = False,
    ) -> None:
        super().__init__(base_url)
        self._timeout = timeout
        self._ssl_verify = ssl_verify

        self._logger = logging.getLogger(self.__class__.__name__)

    def get_all_groups(self) -> list:
        url = f"{self._base_url}{self.url_suffix}/groups"
        self._logger.info(f"Fetching all groups from {url}...")

        response = self._session.get(
            url,
            timeout=self._timeout,
            verify=self._ssl_verify,
        )

        self._check_response(response)

        return response.json()
