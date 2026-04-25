import json
from typing import Any, Mapping

from deps_message_flow.sagas.orchestration import SagaInstance, SerializedSagaData

__all__ = ["SagaInstanceMapper"]


class SagaInstanceMapper:
    @staticmethod
    def to_dict(saga_instance: SagaInstance) -> dict:
        return {
            "saga_type": saga_instance.saga_type,
            "saga_id": saga_instance.saga_id,
            "state_name": saga_instance.state_name,
            "last_request_id": saga_instance.last_request_id,
            "saga_data_type": saga_instance.serialized_saga_data.saga_data_type,
            "saga_data_json": json.loads(saga_instance.serialized_saga_data.saga_data_json),
            "end_state": saga_instance.end_state,
            "compensating": saga_instance.compensating,
            "failed": saga_instance.failed,
        }

    @staticmethod
    def from_dict(saga_dict: Mapping[str, Any]) -> SagaInstance:
        return SagaInstance(
            saga_type=saga_dict["saga_type"],
            saga_id=saga_dict["saga_id"],
            state_name=saga_dict["state_name"],
            last_request_id=saga_dict["last_request_id"],
            serialized_saga_data=SerializedSagaData(
                saga_data_type=saga_dict["saga_data_type"],
                saga_data_json=json.dumps(saga_dict["saga_data_json"]),
            ),
            end_state=saga_dict["end_state"],
            compensating=saga_dict["compensating"],
            failed=saga_dict["failed"],
        )
