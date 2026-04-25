from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field, Json, field_validator

from deps_file.domain.model import WorkflowParamsDict

from ..base import BaseSerializer

__all__ = ["FileProcessRequest"]


class FileProcessRequest(BaseSerializer):
    parsing_features: list[str] = Field(alias="parsingFeatures")
    needs_unifier: bool = Field(alias="needsUnifier")
    needs_extraction: bool = Field(alias="needsExtraction")
    assigned_to_me: bool = Field(alias="assignedToMe")
    engine: str | None = Field(default=None)
    labels: list[str] | None = Field(default=None)
    llm_type: str | None = Field(default=None, alias="llmType")
    language: str | None = Field(default=None)
    metadata: dict | None = Field(default=None)

    @field_validator("engine", "language", "llm_type", mode="before")
    @classmethod
    def convert_null_string(cls, v):
        if v in {"null", "", "None"}:
            return None

        return v

    def workflow_params_to_dict(self) -> WorkflowParamsDict:
        return WorkflowParamsDict(
            parsing_features=self.parsing_features,
            needs_unifier=self.needs_unifier,
            needs_extraction=self.needs_extraction,
            assigned_to_me=self.assigned_to_me,
            llm_type=self.llm_type,
            engine=self.engine,
            language=self.language,
            metadata=self.metadata,
        )
