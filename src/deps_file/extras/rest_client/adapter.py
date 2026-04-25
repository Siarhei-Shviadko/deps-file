from typing import List, Tuple

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__all__ = ["DEPSHTTPSAdapter"]


class DEPSHTTPSAdapter(HTTPAdapter):
    DEFAULT_TIMEOUT: Tuple[float, float] = (3.05, 60)
    TOTAL_RETRIES: int = 8
    BACKOFF_FACTOR: int = 1
    STATUS_FORCELIST: List[int] = [429, 500, 502, 503, 504]
    ALLOWED_METHODS: List[str] = ["GET", "PUT", "HEAD"]

    def __init__(self, *args, **kwargs) -> None:
        kwargs["max_retries"] = Retry(
            total=self.TOTAL_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=self.STATUS_FORCELIST,
            allowed_methods=self.ALLOWED_METHODS,
        )

        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        timeout = kwargs.get("timeout")

        if timeout is None:
            kwargs["timeout"] = self.DEFAULT_TIMEOUT

        return super().send(*args, **kwargs)
