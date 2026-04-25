from dataclasses import dataclass
from typing import TypedDict

from ...shared import Event
from ..processing_params import WorkflowParamsDict

__all__ = ["FileCreated", "ProcessingParamsDict"]


class ProcessingParamsDict(TypedDict):
    group_id: str
    splitting_enabled: bool
    classification_enabled: bool
    workflow_params: WorkflowParamsDict


@dataclass
class FileCreated(Event):
    def __init__(
        self,
        file_id: str,
        name: str,
        path: str,
        processing_params: ProcessingParamsDict,
    ) -> None:
        self.file_id = file_id
        self.name = name
        self.path = path
        self.processing_params = processing_params
