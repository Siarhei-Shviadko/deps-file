from pydantic import BaseModel, ConfigDict

__all__ = ["BaseSerializer"]


class BaseSerializer(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
