from datetime import datetime, timezone

from .events import ProcessingParamsDict
from .events.file_created import FileCreated
from .file import File
from .file_id import FileId
from .processing_params import ProcessingParams, WorkflowParamsDict
from .state import State, Status

__all__ = ["FileFactory"]


class FileFactory:
    @staticmethod
    def create_for_splitting(
        tenant_id: str,
        name: str,
        path: str,
        group_id: str,
        classification_enabled: bool,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None,
    ) -> File:
        return FileFactory.create_file(
            tenant_id=tenant_id,
            name=name,
            path=path,
            group_id=group_id,
            splitting_enabled=True,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
            labels=labels,
        )

    @staticmethod
    def create_for_classification(
        tenant_id: str,
        name: str,
        path: str,
        group_id: str,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None,
    ) -> File:
        return FileFactory.create_file(
            tenant_id=tenant_id,
            name=name,
            path=path,
            group_id=group_id,
            splitting_enabled=False,
            classification_enabled=True,
            workflow_params=workflow_params,
            labels=labels,
        )

    @staticmethod
    def create_for_processing(
        tenant_id: str,
        name: str,
        path: str,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
        group_id: str | None = None,
    ) -> File:
        return FileFactory.create_file(
            tenant_id=tenant_id,
            name=name,
            path=path,
            group_id=group_id,
            splitting_enabled=False,
            classification_enabled=False,
            labels=labels,
            workflow_params=workflow_params,
        )

    @staticmethod
    def create_file(
        tenant_id: str,
        name: str,
        path: str,
        splitting_enabled: bool | None,
        classification_enabled: bool | None,
        workflow_params: WorkflowParamsDict,
        group_id: str | None = None,
        labels: list[str] | None = None,
    ) -> File:
        now = datetime.now(timezone.utc)
        processing_params = ProcessingParams(
            group_id=group_id,
            splitting_enabled=splitting_enabled,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
        )
        state = State(Status.PROCESSING)

        file_id = FileId()
        file = File(
            id_=file_id.value,
            tenant_id=tenant_id,
            name=name,
            path=path,
            state=state,
            processing_params=processing_params,
            labels=labels,
            created_at=now,
            updated_at=now,
            events=[
                FileCreated(
                    file_id=file_id.value,
                    name=name,
                    path=path,
                    processing_params=ProcessingParamsDict(
                        group_id=processing_params.group_id() if processing_params.group_id else None,
                        splitting_enabled=processing_params.splitting_enabled,
                        classification_enabled=processing_params.splitting_enabled,
                        workflow_params=processing_params.workflow_params,  # type: ignore
                    ),
                ),
            ],
        )
        file.generate_pipeline_command()

        return file
