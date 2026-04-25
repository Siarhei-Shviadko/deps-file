import logging

from deps_message_flow.events.publisher import DomainEventPublisher

from deps_file.constants import USER_DESTINATION
from deps_file.domain.exceptions import UserNotFound
from deps_file.domain.model import User, UserFactory
from deps_file.infrastructure.unit_of_work import AbstractUnitOfWork

from ..retry_transaction import retry_on_transaction_error

__all__ = ["CommandUserService"]


class CommandUserService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        domain_event_publisher: DomainEventPublisher,
    ) -> None:
        self._uow = unit_of_work
        self._domain_event_publisher = domain_event_publisher

        self._logger = logging.getLogger(self.__class__.__name__)

    def find_user(self, id_: str) -> User:
        with self._uow:
            user = self._find_user(id_=id_)

        self._logger.info("User with id `%s` found.", id_)

        return user

    @retry_on_transaction_error()
    def save_user(self, id_: str, first_name: str, last_name: str) -> User:
        with self._uow:
            if (user := self._uow.users.user_of_id(id_)) is None:
                user = UserFactory.make(id_=id_, first_name=first_name, last_name=last_name)

            else:
                user.update(first_name=first_name, last_name=last_name)

            self._uow.users.save(user)
            self._publish_events(user)

            self._uow.commit()

        self._logger.info("User with id `%s` saved.", user.id())

        return user

    def _find_user(self, id_: str) -> User:
        if (user := self._uow.users.user_of_id(id_)) is None:
            raise UserNotFound(id_)

        return user

    def _publish_events(self, user: User) -> None:
        self._domain_event_publisher.publish(
            aggregate_type=USER_DESTINATION,
            aggregate_id=user.id(),
            domain_events=user.events,
        )
