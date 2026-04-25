from uuid import uuid4

from deps_message_flow.sagas.orchestration import ISagaInstanceRepository, SagaInstance
from sqlalchemy import insert, select, update

from deps_file.domain.exceptions import NotFoundError
from deps_file.extras import DatabaseSession

from ..tables import saga_table
from .mappers import SagaInstanceMapper

__all__ = ["SagaInstanceRepository"]


class SagaInstanceRepository(ISagaInstanceRepository):
    def __init__(self, database: DatabaseSession):
        self.db = database

    def save(self, saga_instance: SagaInstance) -> SagaInstance:
        saga_instance.saga_id = uuid4().hex
        query = insert(saga_table).values(SagaInstanceMapper.to_dict(saga_instance))

        with self.db.connection() as connection:
            connection.execute(query)

        return saga_instance

    def find(self, saga_id: str) -> SagaInstance:
        query = select(saga_table).where(saga_table.c.saga_id == saga_id)

        with self.db.connection() as connection:
            saga_instance_row = connection.execute(query).mappings().first()

        if not saga_instance_row:
            raise NotFoundError(f"Saga instance with saga_id = {saga_id} not found.")

        return SagaInstanceMapper.from_dict(saga_instance_row)

    def find_for_entity(self, entity_id: str) -> SagaInstance:
        raise NotImplementedError("find_for_entity has not been implemented yet")

    def update(self, saga_instance: SagaInstance) -> SagaInstance:
        fields_to_update = self._get_fields_to_update_from_saga_instance(saga_instance)

        query = (
            update(saga_table).where(saga_table.c.saga_id == saga_instance.saga_id).values(**fields_to_update)
        )  # noqa: WPS221

        with self.db.connection() as connection:
            connection.execute(query)

        return saga_instance

    @staticmethod
    def _get_fields_to_update_from_saga_instance(saga_instance: SagaInstance) -> dict:
        fields_to_update = SagaInstanceMapper.to_dict(saga_instance)
        del fields_to_update["saga_id"]

        return fields_to_update
