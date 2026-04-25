from deps_file.domain.model.group import GroupId
from deps_file.domain.model.shared.guards import Guard, ImmutableCheck

from ...shared import Command
from ..commands import ClassifyFileDomain, ProcessFileDomain, SplitFileDomain
from .workflow_params import WorkflowParamsDict

__all__ = ["ProcessingParams"]


class ProcessingParams:
    group_id = Guard[GroupId](GroupId, ImmutableCheck())
    splitting_enabled = Guard[bool](bool, ImmutableCheck())
    classification_enabled = Guard[bool](bool, ImmutableCheck())
    workflow_params = Guard[WorkflowParamsDict](dict, ImmutableCheck())

    def __init__(
        self,
        group_id: str | None,
        splitting_enabled: bool,
        classification_enabled: bool,
        workflow_params: WorkflowParamsDict,
    ) -> None:
        if group_id:
            self.group_id = GroupId(group_id)
        self.splitting_enabled = splitting_enabled
        self.classification_enabled = classification_enabled
        self.workflow_params = workflow_params

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return (
            self.group_id == other.group_id
            and self.splitting_enabled == other.splitting_enabled
            and self.classification_enabled == other.classification_enabled
            and self.workflow_params == other.workflow_params
        )

    def __repr__(self) -> str:
        return (
            f"<class '{self.__class__.__name__}': "
            f"{self.group_id=},"
            f"{self.splitting_enabled=},"
            f"{self.classification_enabled=},"
            f"{self.workflow_params=}>"  # noqa: C812
        )

    @property
    def metadata(self) -> dict | None:
        return self.workflow_params.get("metadata")

    def generate_command(self) -> Command:
        if self._check_splitting_command():
            return self._add_splitting_command()
        elif self._check_classification_command():
            return self._add_classification_command()
        return self._add_processing_command()

    def _check_splitting_command(self) -> bool:
        return bool(self.splitting_enabled and self.group_id)

    def _check_classification_command(self) -> bool:
        return bool(self.classification_enabled and self.group_id and not self.splitting_enabled)

    def _add_splitting_command(self) -> SplitFileDomain:
        return SplitFileDomain(
            group_id=self.group_id(),
            classification_enabled=self.classification_enabled,
            document_type_id=self.workflow_params.get("document_type_id"),
            parsing_features=self.workflow_params.get("parsing_features"),
            engine=self.workflow_params.get("engine"),
            language=self.workflow_params.get("language"),
            llm_type=self.workflow_params.get("llm_type"),
            needs_unifier=self.workflow_params.get("needs_unifier", False),
            needs_extraction=self.workflow_params.get("needs_extraction", True),
            assigned_to_me=self.workflow_params.get("assigned_to_me", False),
            metadata=self.metadata,
        )

    def _add_classification_command(self) -> ClassifyFileDomain:
        return ClassifyFileDomain(
            group_id=self.group_id(),
            parsing_features=self.workflow_params.get("parsing_features"),
            engine=self.workflow_params.get("engine"),
            language=self.workflow_params.get("language"),
            llm_type=self.workflow_params.get("llm_type"),
            needs_unifier=self.workflow_params.get("needs_unifier", False),
            needs_extraction=self.workflow_params.get("needs_extraction", False),
            assigned_to_me=self.workflow_params.get("assigned_to_me", False),
            metadata=self.metadata,
        )

    def _add_processing_command(self) -> ProcessFileDomain:
        return ProcessFileDomain(
            parsing_features=self.workflow_params.get("parsing_features"),
            engine=self.workflow_params.get("engine"),
            language=self.workflow_params.get("language"),
        )
