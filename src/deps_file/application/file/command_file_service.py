import logging
import os
import uuid

from deps_message_flow.commands.producer import CommandProducer
from deps_message_flow.events.publisher import DomainEventPublisher
from deps_object_storage import ObjectStorage

from deps_file.constants import (
    BATCH_COMMANDS_CHANNEL,
    COMMANDS_CHANNEL,
    COMMANDS_REPLIES_CHANNEL,
    DOCUMENT_COMMANDS_CHANNEL,
)
from deps_file.domain.exceptions import FileNotFound, GroupNotFound
from deps_file.domain.model import (
    ClassifyFileDomain,
    File,
    FileFactory,
    ProcessFileDomain,
    SplitFileDomain,
    WorkflowParamsDict,
)
from deps_file.infrastructure.unit_of_work import AbstractUnitOfWork
from deps_file.messaging.commands import DeleteBatchesWithDocuments, DeleteDocument

from ..retry_transaction import retry_on_transaction_error
from .batch_proxy import BatchFileDict, IBatchProxy
from .document_proxy import IDocumentProxy

__all__ = ["CommandFileService"]


class CommandFileService:  # noqa: WPS214
    AGGREGATE_TYPE = "File"
    command_mapper = {
        ProcessFileDomain: (COMMANDS_CHANNEL, COMMANDS_REPLIES_CHANNEL),
        ClassifyFileDomain: (COMMANDS_CHANNEL, COMMANDS_REPLIES_CHANNEL),
        SplitFileDomain: (COMMANDS_CHANNEL, COMMANDS_REPLIES_CHANNEL),
    }

    def __init__(
        self,
        object_storage: ObjectStorage,
        unit_of_work: AbstractUnitOfWork,
        domain_event_publisher: DomainEventPublisher,
        document_proxy: IDocumentProxy,
        batch_proxy: IBatchProxy,
        command_producer=CommandProducer,
    ) -> None:
        self._object_storage = object_storage
        self._uow = unit_of_work
        self._domain_event_publisher = domain_event_publisher
        self._document_proxy = document_proxy
        self._command_producer = command_producer
        self._batch_proxy = batch_proxy

        self._logger = logging.getLogger(self.__class__.__name__)

    def split(
        self,
        tenant_id: str,
        name: str,
        content: bytes,
        group_id: str,
        classification_enabled: bool,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        file_path = self._upload_file_to_storage(name, content)
        return self.create_file_for_splitting(
            tenant_id=tenant_id,
            name=name,
            file_path=file_path,
            group_id=group_id,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
            labels=labels,
        )

    @retry_on_transaction_error()
    def create_file_for_splitting(
        self,
        tenant_id: str,
        name: str,
        file_path: str,
        group_id: str,
        classification_enabled: bool,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        with self._uow:
            self._ensure_group_exists(group_id, tenant_id)

            file = FileFactory.create_for_splitting(
                tenant_id=tenant_id,
                name=name,
                path=file_path,
                group_id=group_id,
                classification_enabled=classification_enabled,
                workflow_params=workflow_params,
                labels=labels,
            )

            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)
        self._publish_events(file)

        return file

    def classify(
        self,
        tenant_id: str,
        name: str,
        content: bytes,
        group_id: str,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        file_path = self._upload_file_to_storage(name, content)
        return self.create_file_for_classification(tenant_id, name, file_path, group_id, workflow_params, labels)

    @retry_on_transaction_error()
    def create_file_for_classification(
        self,
        tenant_id: str,
        name: str,
        file_path: str,
        group_id: str,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        with self._uow:
            self._ensure_group_exists(group_id, tenant_id)

            file = FileFactory.create_for_classification(
                tenant_id=tenant_id,
                name=name,
                path=file_path,
                group_id=group_id,
                workflow_params=workflow_params,
                labels=labels,
            )

            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)
        self._publish_events(file)

        return file

    def process(
        self,
        tenant_id: str,
        name: str,
        content: bytes,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        file_path = self._upload_file_to_storage(name, content)
        return self.create_file_for_processing(tenant_id, name, file_path, workflow_params, labels)

    @retry_on_transaction_error()
    def create_file_for_processing(
        self,
        tenant_id: str,
        name: str,
        file_path: str,
        workflow_params: WorkflowParamsDict,
        labels: list[str] | None = None,
    ) -> File:
        file = FileFactory.create_for_processing(
            tenant_id=tenant_id,
            name=name,
            path=file_path,
            workflow_params=workflow_params,
            labels=labels,
        )

        with self._uow:
            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)
        self._publish_events(file)

        return file

    @retry_on_transaction_error()
    def split_file(
        self,
        file_id: str,
        tenant_id: str,
        group_id: str,
        classification_enabled: bool,
        workflow_params: WorkflowParamsDict,
    ) -> None:
        with self._uow:
            self._ensure_group_exists(group_id, tenant_id)
            file = self._get_file_or_raise(file_id, tenant_id)
            file.split(group_id, classification_enabled, workflow_params)

            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)
        self._publish_events(file)

    @retry_on_transaction_error()
    def classify_file(
        self,
        file_id: str,
        tenant_id: str,
        group_id: str,
        workflow_params: WorkflowParamsDict,
    ) -> None:
        with self._uow:
            self._ensure_group_exists(group_id, tenant_id)
            file = self._get_file_or_raise(file_id, tenant_id)
            file.classify(group_id, workflow_params)

            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)

    def create_document_from_file(
        self,
        file_id: str,
        tenant_id: str,
        document_type_id: str,
    ) -> tuple[str, str]:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)

        file.check_reference_existence()

        file_content = self._get_content(file.path)
        document_id, document_name = self._create_document(
            file_name=file.name,
            file_content=file_content,
            document_type_id=document_type_id,
            workflow_params=file.processing_params.workflow_params,
        )

        try:
            self._save_document_reference(file_id, tenant_id, document_id, document_name)
        except Exception as e:
            self._logger.error(
                f"Failed to save document reference {document_id} to file {file_id}. "
                f"Deleting document as compensation: {e}",
            )
            self._delete_document_compensation(document_id)
            raise

        return document_id, document_name

    def create_batch_from_file(
        self,
        file_id: str,
        tenant_id: str,
        batch_name: str,
        batch_files: list[BatchFileDict],
        group_id: str | None,
    ) -> str:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)

        file.check_reference_existence()

        batch_id, batch_name = self._create_batch(
            batch_name=batch_name,
            batch_files=batch_files,
            group_id=group_id,
            workflow_params=file.processing_params.workflow_params,
        )

        try:
            self._save_batch_reference(file_id, tenant_id, batch_id, batch_name)
        except Exception as error:
            self._logger.error(
                "Failed to save batch reference %s to file %s. Deleting batch as compensation: %s",
                batch_id,
                file_id,
                error,
            )
            self._delete_batch_compensation(batch_id)
            raise

        return batch_id

    @retry_on_transaction_error()
    def restart_file(self, file_id: str, tenant_id: str) -> None:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.restart()

            self._uow.files.save(file)
            self._uow.commit()

        self._send_commands(file)
        self._publish_events(file)

    @retry_on_transaction_error()
    def delete_files(self, ids: set[str], tenant_id: str) -> None:
        with self._uow:
            self._delete_files(ids, tenant_id)

    @retry_on_transaction_error()
    def complete_processing(self, file_id: str, tenant_id: str) -> None:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.complete_processing()

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    @retry_on_transaction_error()
    def fail_processing(self, file_id: str, tenant_id: str, error_message: str) -> None:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.fail_processing(error_message)

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    @retry_on_transaction_error()
    def complete_classification(
        self,
        file_id: str,
        tenant_id: str,
        document_id: str,
        document_name: str,
        document_type_id: str,
    ) -> None:
        self._logger.info(f"Adding reference to file {file_id} for document {document_id} of type {document_type_id}")

        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.complete_classification(document_id, document_name)

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    @retry_on_transaction_error()
    def fail_classification(self, file_id: str, tenant_id: str, error_message: str) -> None:
        self._logger.info(f"Setting failed state for file {file_id} due to classification failure")
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.fail_classification(error_message)

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    @retry_on_transaction_error()
    def complete_splitting(
        self,
        file_id: str,
        tenant_id: str,
        batch_id: str,
        batch_name: str,
    ) -> None:
        self._logger.info("Adding reference to file %s for batch %s", file_id, batch_id)

        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.complete_splitting(entity_id=batch_id, entity_name=batch_name)

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    @retry_on_transaction_error()
    def fail_splitting(self, file_id: str, tenant_id: str, error_message: str) -> None:
        self._logger.info("Setting failed state for file {file_id} due to splitting failure")
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)
            file.fail_splitting(error_message)

            self._uow.files.save(file)
            self._uow.commit()

        self._publish_events(file)

    def get_file_content(self, file_id: str, tenant_id: str) -> tuple[bytes, str]:
        with self._uow:
            file = self._get_file_or_raise(file_id, tenant_id)

        content = self._get_content(file.path)
        return content, file.name

    @retry_on_transaction_error()
    def _save_document_reference(
        self,
        file_id: str,
        tenant_id: str,
        document_id: str,
        document_name: str,
    ) -> None:
        with self._uow:
            file = self._get_file_or_raise(file_id=file_id, tenant_id=tenant_id)
            file.add_document_reference(document_id, document_name)
            self._uow.files.save(file)
            self._uow.commit()

            self._logger.info(f"Successfully saved document reference {document_id} to file {file_id}")

    def _publish_events(self, file: File) -> None:
        self._domain_event_publisher.publish(
            aggregate_type=self.AGGREGATE_TYPE,
            aggregate_id=file.id(),
            domain_events=file.events,
        )

    def _send_commands(self, file: File) -> None:
        for command in file.commands:
            channel, reply_to = self.command_mapper[type(command)]
            self._command_producer.send(
                channel=channel,
                command=command,
                reply_to=reply_to,
            )

    @staticmethod
    def _generate_unique_file_name(file_name: str) -> str:
        _, ext = os.path.splitext(file_name)
        return uuid.uuid4().hex + ext

    def _upload_file_to_storage(self, file_name: str, content: bytes) -> str:
        unique_file_name = self._generate_unique_file_name(file_name)
        return self._object_storage.upload(unique_file_name, content, replace_if_exists=True)

    def _delete_files(self, ids: set[str], tenant_id: str) -> None:
        files = self._uow.files.files_of_ids(ids, tenant_id)

        if files:
            for file in files:
                file.delete()

            self._uow.files.delete_all(files)
            self._uow.commit()

        for file in files:
            self._publish_events(file)

    def _ensure_group_exists(self, group_id: str, tenant_id: str) -> None:
        if self._uow.groups.group_of_id(group_id, tenant_id) is None:
            raise GroupNotFound(group_id)

    def _get_file_or_raise(self, file_id: str, tenant_id: str) -> File:
        file = self._uow.files.file_of_id(file_id, tenant_id)
        if file is None:
            raise FileNotFound(file_id)

        return file

    def _get_content(self, file_path: str) -> bytes:
        return self._object_storage.download(file_path)

    def _create_document(
        self,
        file_name: str,
        file_content: bytes,
        document_type_id: str,
        workflow_params: WorkflowParamsDict,
    ) -> tuple[str, str]:
        document_id, document_name = self._document_proxy.create_document_from_file(
            file_name=file_name,
            file_content=file_content,
            document_type_id=document_type_id,
            engine=workflow_params["engine"],
            language=workflow_params["language"],
            llm_type=workflow_params["llm_type"],
            parsing_features=workflow_params["parsing_features"],
            needs_unification=True,
            needs_extraction=True,
            assign_to_me=workflow_params["assigned_to_me"],
            metadata=workflow_params["metadata"],
        )

        return document_id, document_name

    def _delete_document_compensation(self, document_id: str) -> None:
        self._command_producer.send(
            DOCUMENT_COMMANDS_CHANNEL,
            DeleteDocument(document_id=document_id),
            COMMANDS_REPLIES_CHANNEL,
        )

    @retry_on_transaction_error()
    def _save_batch_reference(
        self,
        file_id: str,
        tenant_id: str,
        batch_id: str,
        batch_name: str,
    ) -> None:
        with self._uow:
            file = self._get_file_or_raise(file_id=file_id, tenant_id=tenant_id)
            file.add_batch_reference(entity_id=batch_id, entity_name=batch_name)
            self._uow.files.save(file)
            self._uow.commit()

            self._logger.info(f"Successfully saved batch reference {batch_id} to file {file_id}")

    def _create_batch(
        self,
        batch_name: str,
        batch_files: list[BatchFileDict],
        group_id: str | None,
        workflow_params: WorkflowParamsDict,
    ) -> tuple[str, str]:
        batch_id, batch_name = self._batch_proxy.create_batch_from_files(
            batch_name=batch_name,
            files=batch_files,
            group_id=group_id,
            metadata=workflow_params["metadata"],
            engine=workflow_params["engine"],
            language=workflow_params["language"],
            llm_type=workflow_params["llm_type"],
            parsing_features=workflow_params["parsing_features"],
        )

        return batch_id, batch_name

    def _delete_batch_compensation(self, batch_id: str) -> None:
        self._command_producer.send(
            BATCH_COMMANDS_CHANNEL,
            DeleteBatchesWithDocuments(batch_ids=[batch_id]),
            COMMANDS_REPLIES_CHANNEL,
        )
