import pytest
from deps_message_flow.sagas.testing_support import *

from deps_file.constants import SPLIT_COMMANDS_CHANNEL
from deps_file.domain.model import ErrorCode, ReferenceType, Status
from deps_file.messaging import ErrorType
from deps_file.messaging.orchestration.splitting import SplitFile, SplitFileReply


@pytest.mark.usefixtures("add_files")
def test_splitting__success(
    splitting_suts,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    batch_id,
    batch_name,
    command_file_repository,
):
    saga_data = splitting_suts.saga_data
    splitting_suts = (
        splitting_suts.expect()
        .command(
            SplitFile(
                file_id=test_file_1.id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                document_type_id=saga_data["document_type_id"],
                classification_enabled=saga_data["classification_enabled"],
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
            )
        )
        .to(SPLIT_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            SplitFileReply(
                file_id=test_file_1.id(),
                batch_id=batch_id,
                batch_name=batch_name,
                error_type=None,
                error_message=None,
            )
        )
        .expect_completed_successfully()
    )

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.COMPLETED
    assert file.state.error_message is None
    assert file.reference.entity_id == batch_id
    assert file.reference.entity_name == batch_name
    assert file.reference.entity_type == ReferenceType.BATCH


@pytest.mark.usefixtures("add_files")
def test_splitting__system_failure(
    splitting_suts,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    error_message,
    command_file_repository,
):
    saga_data = splitting_suts.saga_data
    splitting_suts = (
        splitting_suts.expect()
        .command(
            SplitFile(
                file_id=test_file_1.id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                document_type_id=saga_data["document_type_id"],
                classification_enabled=saga_data["classification_enabled"],
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
            )
        )
        .to(SPLIT_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            SplitFileReply(
                file_id=test_file_1.id(),
                error_type=ErrorType.SYSTEM.value,
                error_message=error_message,
            )
        )
        .expect_completed_successfully()
    )

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_SPLITTING
    assert file.reference is None


@pytest.mark.usefixtures("add_files")
def test_splitting__business_failure(
    splitting_suts,
    test_file_1,
    test_group_1_id,
    engine,
    parsing_features,
    language,
    llm_type,
    error_message,
    command_file_repository,
):
    saga_data = splitting_suts.saga_data
    splitting_suts = (
        splitting_suts.expect()
        .command(
            SplitFile(
                file_id=test_file_1.id(),
                file_name=test_file_1.name,
                group_id=test_group_1_id(),
                file_path=test_file_1.path,
                document_type_id=saga_data["document_type_id"],
                classification_enabled=saga_data["classification_enabled"],
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=False,
                needs_extraction=True,
                assigned_to_me=False,
                metadata={"test_key": "test_value"},
            )
        )
        .to(SPLIT_COMMANDS_CHANNEL)
        .and_given()
        .success_reply(
            SplitFileReply(
                file_id=test_file_1.id(),
                error_type=ErrorType.BUSINESS.value,
                error_message=error_message,
            )
        )
        .expect_completed_successfully()
    )

    file = command_file_repository.file_of_id(id_=test_file_1.id(), tenant_id=test_file_1.tenant_id())
    assert file.status == Status.FAILED
    assert file.state.error_message == error_message
    assert file.state.error_code == ErrorCode.FAIL_SPLITTING
    assert file.reference is None
