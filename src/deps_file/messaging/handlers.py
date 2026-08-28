import logging

from dependency_injector.wiring import Provide, inject
from deps_message_flow.commands.consumer.command_message import CommandMessage
from deps_message_flow.events.subscriber.domain_event_envelope import (
    DomainEventEnvelope,
)

from deps_file.application import (
    CommandFileService,
    CommandGroupService,
    SagaFileService,
)
from deps_file.containers import Containers
from deps_file.domain.model import ClassifyFileDomain, ProcessFileDomain
from deps_file.messaging.events import (
    SplitFileExecuted,
    SplittingProposalAwaitingReview,
)

from .commands import (
    DeleteFile,
    ImportFileForClassification,
    ImportFileForProcessing,
    ImportFileForSplitting,
)

logger = logging.getLogger(__name__)


def test_event_handler(dee: DomainEventEnvelope) -> None:
    pass


def test_command_handler(command_message: CommandMessage):
    pass


@inject
def group_created_handler(
    dee: DomainEventEnvelope,
    group_service: CommandGroupService = Provide[Containers.command_group_service],
):
    logger.info(f"Group created: {dee}")
    group_service.create(
        group_id=dee.event.id,
        tenant_id=dee.event.tenant_id,
    )


@inject
def group_deleted_handler(
    dee: DomainEventEnvelope,
    group_service: CommandGroupService = Provide[Containers.command_group_service],
):
    logger.info(f"Group deleted: {dee}")
    group_service.delete(group_id=dee.event.id, tenant_id=dee.event.tenant_id)


@inject
def process_file_handler(
    command_message: CommandMessage[ProcessFileDomain],
    saga_file_service=Provide[Containers.saga_file_service],
):
    command = command_message.command

    saga_file_service.process_file(
        file_id=command.file_id,
        tenant_id=command.tenant_id,
        files=command.files,
        engine=command.engine,
        language=command.language,
        parsing_features=command.parsing_features,
    )


@inject
def classify_file_handler(
    command_message: CommandMessage[ClassifyFileDomain],
    tenant_id: str = Provide[Containers.current_user_tenant],
    saga_file_service: SagaFileService = Provide[Containers.saga_file_service],
):
    command = command_message.command

    saga_file_service.classify_file(
        file_id=command.file_id,
        tenant_id=tenant_id,
        file_path=command.path,
        file_name=command.file_name,
        group_id=command.group_id,
        engine=command.engine,
        language=command.language,
        parsing_features=command.parsing_features,
        llm_type=command.llm_type,
        needs_unifier=command.needs_unifier,
        needs_extraction=command.needs_extraction,
        assigned_to_me=command.assigned_to_me,
        metadata=command.metadata,
    )


@inject
def import_file_for_processing_handler(
    command_message: CommandMessage[ImportFileForProcessing],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
):
    command = command_message.command

    command_file_service.create_file_for_processing(
        tenant_id=tenant_id,
        name=command.file_name,
        file_path=command.file_path,
        workflow_params=command.workflow_params,
    )


@inject
def import_file_for_classification_handler(
    command_message: CommandMessage[ImportFileForClassification],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
):
    command = command_message.command

    command_file_service.create_file_for_classification(
        tenant_id=tenant_id,
        name=command.file_name,
        file_path=command.file_path,
        group_id=command.group_id,
        workflow_params=command.workflow_params,
    )


@inject
def import_file_for_splitting_handler(
    command_message: CommandMessage[ImportFileForSplitting],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
):
    command = command_message.command

    command_file_service.create_file_for_splitting(
        tenant_id=tenant_id,
        name=command.file_name,
        file_path=command.file_path,
        group_id=command.group_id,
        classification_enabled=command.classification_enabled,
        workflow_params=command.workflow_params,
    )


@inject
def delete_file_handler(
    command_message: CommandMessage[DeleteFile],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
) -> None:
    command_file_service.delete_files(ids=set(command_message.command.file_ids), tenant_id=tenant_id)


@inject
def split_file_executed_handler(
    dee: DomainEventEnvelope[SplitFileExecuted],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
) -> None:
    event = dee.event
    if event.error_type is None:
        command_file_service.complete_splitting(
            file_id=event.file_id,
            tenant_id=tenant_id,
            batch_id=event.batch_id,
            batch_name=event.batch_name,
        )
    else:
        command_file_service.fail_splitting(
            file_id=event.file_id,
            tenant_id=tenant_id,
            error_message=event.error_message,
        )


@inject
def splitting_proposal_awaiting_review_handler(
    dee: DomainEventEnvelope[SplittingProposalAwaitingReview],
    tenant_id: str = Provide[Containers.current_user_tenant],
    command_file_service: CommandFileService = Provide[Containers.command_file_service],
) -> None:
    command_file_service.set_splitting_review(
        file_id=dee.event.proposal_id,
        tenant_id=tenant_id,
    )
