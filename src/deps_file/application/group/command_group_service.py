import logging

from deps_message_flow.commands.producer import CommandProducer
from deps_message_flow.events.publisher import DomainEventPublisher

from deps_file.domain.exceptions import GroupNotFound
from deps_file.domain.model import Group, GroupFactory
from deps_file.infrastructure.repositories import GroupMapper
from deps_file.infrastructure.unit_of_work import AbstractUnitOfWork

from ..retry_transaction import retry_on_transaction_error
from .group_proxy import IGroupProxy

__all__ = ["CommandGroupService"]


class CommandGroupService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        command_producer: CommandProducer,
        domain_event_publisher: DomainEventPublisher,
        group_proxy: IGroupProxy,
    ) -> None:
        self._uow = unit_of_work
        self._command_producer = command_producer
        self._domain_event_publisher = domain_event_publisher
        self._group_proxy = group_proxy

        self._logger = logging.getLogger(self.__class__.__name__)

    @retry_on_transaction_error()
    def initialize(self):
        try:
            groups = self._group_proxy.get_all_groups()

            with self._uow:
                self._uow.groups.sync_groups(groups=[GroupMapper.from_dict(group) for group in groups])
                self._uow.commit()

        except Exception as err:
            self._logger.error(
                "Failed to sync groups: %s",
                str(err),
                exc_info=True,
            )
        else:
            self._logger.info("Successfully synced groups.")

    @retry_on_transaction_error()
    def create(
        self,
        group_id: str,
        tenant_id: str,
    ) -> Group:
        with self._uow:
            group = GroupFactory.create(
                id_=group_id,
                tenant_id=tenant_id,
            )

            self._uow.groups.save(group)

            self._uow.commit()

        self._logger.info(f"Group {group_id} is saved.")

        return group

    @retry_on_transaction_error()
    def delete(self, group_id: str, tenant_id: str) -> Group:
        with self._uow:
            group = self._find_group(group_id, tenant_id)

            group.delete()

            self._uow.groups.delete(group)
            self._uow.commit()

        self._logger.info("Group %s is deleted.", group_id)

        return group

    def _find_group(self, group_id: str, tenant_id: str) -> Group:
        if (group := self._uow.groups.group_of_id(group_id, tenant_id)) is None:
            raise GroupNotFound(group_id=group_id)

        return group
