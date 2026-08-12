import random
import uuid

import pytest
from deps_message_flow.sagas.testing_support import *

from deps_file.messaging.orchestration.classification import (
    ClassifySaga,
    ClassifySagaData,
)
from deps_file.messaging.orchestration.processing import (
    ProcessingSaga,
    ProcessingSagaData,
)


@pytest.fixture
def language():
    return random.choice([None, "en", "es"])


@pytest.fixture
def engine():
    return random.choice([None, "Tesseract", "GCP Document AI"])


@pytest.fixture
def llm_type():
    return random.choice([None, "GPT-4", "Claude"])


@pytest.fixture
def parsing_features():
    return [uuid.uuid4().hex]


@pytest.fixture
def suts(
    test_file_1_id,
    tenant_id,
    test_file_1,
    engine,
    parsing_features,
    language,
    command_file_service,
    add_files,
) -> SagaUnitTestSupport:
    return SagaUnitTestSupport.given().saga(
        ProcessingSaga(
            command_file_service=command_file_service,
        ),
        ProcessingSagaData(
            test_file_1_id(),
            tenant_id(),
            [test_file_1.path],
            parsing_features,
            engine,
            language,
        ),
    )


@pytest.fixture
def classification_suts(
    test_file_1_id,
    tenant_id,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    command_file_service,
    add_files,
) -> SagaUnitTestSupport:
    return SagaUnitTestSupport.given().saga(
        ClassifySaga(
            command_file_service=command_file_service,
        ),
        ClassifySagaData(
            file_id=test_file_1_id(),
            tenant_id=tenant_id(),
            file_path=test_file_1.path,
            file_name=test_file_1.name,
            group_id=test_group_1_id(),
            parsing_features=parsing_features,
            engine=engine,
            language=language,
            llm_type=llm_type,
            needs_unifier=False,
            needs_extraction=True,
            assigned_to_me=False,
            metadata={"test_key": "test_value"},
        ),
    )
