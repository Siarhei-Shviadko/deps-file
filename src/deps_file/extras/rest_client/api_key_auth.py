from typing import Dict

import requests

__all__ = ["DEPSApiKeyAuth"]


class DEPSApiKeyAuth(requests.auth.AuthBase):
    API_KEY_HEADER = "API-Key"

    def __init__(self, api_key: str):
        self._auth_header = self._create_api_key_header(api_key)

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers.update(self._auth_header)

        return request

    def _create_api_key_header(self, api_key: str) -> dict[str, str]:
        return {self.API_KEY_HEADER: api_key}
