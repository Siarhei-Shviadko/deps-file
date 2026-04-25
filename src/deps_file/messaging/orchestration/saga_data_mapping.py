from deps_message_flow.sagas.orchestration import SagaDataMapping

from .classification import ClassifySagaData
from .processing import ProcessingSagaData
from .splitting import SplitSagaData

__all__ = ["make_saga_data_mapping"]


def make_saga_data_mapping() -> SagaDataMapping:
    return SagaDataMapping(
        {
            ProcessingSagaData.__name__: ProcessingSagaData,
            ClassifySagaData.__name__: ClassifySagaData,
            SplitSagaData.__name__: SplitSagaData,
        },
    )
