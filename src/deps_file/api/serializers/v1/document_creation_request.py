from pydantic import Field

from ..base import BaseSerializer

__all__ = ["DocumentCreationRequest"]


class DocumentCreationRequest(BaseSerializer):
    document_type_id: str = Field(..., alias="documentTypeId")
