from pydantic import Field

from ..base import BaseSerializer

__all__ = ["BatchCreationResponse"]


class BatchCreationResponse(BaseSerializer):
    batch_id: str = Field(..., alias="batchId")
