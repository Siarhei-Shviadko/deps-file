from pydantic import Field

from deps_file.api.serializers import BaseSerializer

__all__ = ["FileReferenceInfoResponse"]


class FileReferenceInfoResponse(BaseSerializer):
    entity_type: str = Field(..., alias="entityType")
    entity_id: str = Field(..., alias="entityId")
    entity_name: str = Field(..., alias="entityName")
