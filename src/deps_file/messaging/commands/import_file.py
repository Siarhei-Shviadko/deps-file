from dataclasses import dataclass

from deps_message_flow.commands.common import Command

from deps_file.domain.model import WorkflowParamsDict

__all__ = ["ImportFileForProcessing", "ImportFileForClassification", "ImportFileForSplitting"]


@dataclass
class ImportFileForProcessing(Command):
    file_name: str
    file_path: str
    workflow_params: WorkflowParamsDict


@dataclass
class ImportFileForClassification(Command):
    file_name: str
    file_path: str
    group_id: str
    workflow_params: WorkflowParamsDict


@dataclass
class ImportFileForSplitting(Command):
    file_name: str
    file_path: str
    group_id: str
    classification_enabled: bool
    workflow_params: WorkflowParamsDict
