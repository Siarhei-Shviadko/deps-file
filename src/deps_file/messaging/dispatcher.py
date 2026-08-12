import logging

from deps_message_flow.commands.consumer import (
    CommandDispatcher,
    CommandHandlersBuilder,
)
from deps_message_flow.events.subscriber import (
    DomainEventDispatcher,
    DomainEventHandlersBuilder,
)
from deps_message_flow.messaging.consumer import IMessageConsumer
from deps_message_flow.messaging.producer import IMessageProducer

from deps_file.constants import (
    COMMANDS_CHANNEL,
    COMMANDS_QUEUE,
    COMMANDS_REPLIES_CHANNEL,
    DOCUMENTS_EXCHANGER,
    EVENTS_QUEUE,
    GROUP_DESTINATION,
    SPLITTING_PROPOSAL_DESTINATION,
)
from deps_file.domain.events import TestCommandReply, TestEvent
from deps_file.domain.model import (
    ClassifyFileDomain,
    GroupCreated,
    GroupDeleted,
    ProcessFileDomain,
)
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

_logger = logging.getLogger(__name__)


def make_message_dispatcher(subscriber: IMessageConsumer, producer: IMessageProducer) -> IMessageConsumer:
    from deps_file.messaging.handlers import (  # noqa: WPS433
        classify_file_handler,
        delete_file_handler,
        group_created_handler,
        group_deleted_handler,
        import_file_for_classification_handler,
        import_file_for_processing_handler,
        import_file_for_splitting_handler,
        process_file_handler,
        split_file_executed_handler,
        splitting_proposal_awaiting_review_handler,
        test_command_handler,
        test_event_handler,
    )

    events_handlers = (
        DomainEventHandlersBuilder.for_aggregate_type(GROUP_DESTINATION)
        .on_event(GroupCreated, group_created_handler)
        .on_event(GroupDeleted, group_deleted_handler)
        .and_for_aggregate_type(DOCUMENTS_EXCHANGER)
        .on_event(TestEvent, test_event_handler)
        .and_for_aggregate_type(SPLITTING_PROPOSAL_DESTINATION)
        .on_event(SplitFileExecuted, split_file_executed_handler)
        .on_event(SplittingProposalAwaitingReview, splitting_proposal_awaiting_review_handler)
        .for_queue(EVENTS_QUEUE)
        .build()
    )

    commands_handlers = (
        CommandHandlersBuilder.from_channel(COMMANDS_REPLIES_CHANNEL)
        .on_message(TestCommandReply, test_command_handler)
        .and_from_channel(COMMANDS_CHANNEL)
        .on_message(ProcessFileDomain, process_file_handler)
        .on_message(ClassifyFileDomain, classify_file_handler)
        .on_message(ImportFileForProcessing, import_file_for_processing_handler)
        .on_message(ImportFileForClassification, import_file_for_classification_handler)
        .on_message(ImportFileForSplitting, import_file_for_splitting_handler)
        .on_message(DeleteFile, delete_file_handler)
        .for_queue(COMMANDS_QUEUE)
        .build()
    )

    ded = DomainEventDispatcher(events_handlers, subscriber)
    ded.initialize()

    cd = CommandDispatcher(commands_handlers, subscriber, producer)
    cd.initialize()

    _logger.info("Start consuming....")

    return subscriber
