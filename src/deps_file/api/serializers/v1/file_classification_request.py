from pydantic import Field, field_validator

from ..base import BaseSerializer

__all__ = ["BaseFileClassificationRequest", "FileClassificationRequest"]


class BaseFileClassificationRequest(BaseSerializer):
    group_id: str = Field(..., alias="groupId")
    engine: str | None = None
    language: str | None = None
    llm_type: str | None = Field(None, alias="llmType")
    parsing_features: list[str] | None = Field(None, alias="parsingFeatures")
    needs_unifier: bool = Field(..., alias="needsUnifier")
    needs_extraction: bool = Field(..., alias="needsExtraction")
    assigned_to_me: bool = Field(..., alias="assignedToMe")
    metadata: dict | None = None

    @field_validator("engine", "language", "llm_type", mode="before")
    @classmethod
    def convert_null_string(cls, v):
        if v in {"null", "", "None"}:
            return None

        return v

    def to_workflow_params_dict(self) -> dict:
        return {
            "engine": self.engine,
            "language": self.language,
            "llm_type": self.llm_type,
            "parsing_features": self.normalize_str_list(self.parsing_features),
            "needs_unifier": self.needs_unifier,
            "needs_extraction": self.needs_extraction,
            "assigned_to_me": self.assigned_to_me,
            "metadata": self.metadata or {},
        }

    @staticmethod
    def normalize_str_list(items: list[str] | None) -> list:
        if not items:
            return []
        result: list = []
        for item in items:
            result.extend(x.strip() for x in item.split(",") if x.strip())
        return result


class FileClassificationRequest(BaseFileClassificationRequest):
    labels: list[str] | None = None

    @property
    def normalized_labels(self) -> list[str]:
        return self.normalize_str_list(self.labels)
