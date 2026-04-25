from io import BytesIO
from uuid import uuid4

import pytest
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from deps_file.domain.model import FileFactory
from deps_file.domain.model.file import WorkflowParamsDict
from deps_file.domain.model.file.constants import (
    MAX_FILE_NAME_LENGTH,
    MAX_FILE_PATH_LENGTH,
)
from deps_file.infrastructure.repositories.tables import file_label_table, label_table
from tests.factories import GroupFactory

pytest_plugins = [
    "tests.shared_fixtures.file.endpoints_fixtures",
    "tests.shared_fixtures.file.file_fixtures",
    "tests.shared_fixtures.file_reference.file_reference_fixtures",
    "tests.shared_fixtures.group.group_fixtures",
]


@pytest.fixture
def unit_of_work(containers):
    unit_of_work = containers.unit_of_work()

    with unit_of_work:
        yield unit_of_work


@pytest.fixture
def query_user_repository(repositories):
    return repositories.query_user()


@pytest.fixture
def command_file_service(containers):
    return containers.command_file_service()


@pytest.fixture()
def add_users(unit_of_work, test_users):
    for user in test_users:
        unit_of_work.users.save(user)
    unit_of_work.commit()


@pytest.fixture
def fake_file_name(fake):
    return fake.file_name(extension="pdf")


@pytest.fixture
def fake_file_path(fake, fake_file_name):
    directories = "/".join(["uploads"] + fake.words(nb=3))
    return f"/{directories}/{fake_file_name}"


@pytest.fixture
def integration_file_with_complete_data(
    test_file_1_tenant_id,
    test_processing_params_full,
    fake_file_name,
    fake_file_path,
):
    return FileFactory.create_file(
        tenant_id=test_file_1_tenant_id(),
        name=fake_file_name,
        path=fake_file_path,
        group_id=(test_processing_params_full.group_id.value if test_processing_params_full.group_id else None),
        splitting_enabled=test_processing_params_full.splitting_enabled,
        classification_enabled=(test_processing_params_full.classification_enabled),
        workflow_params=test_processing_params_full.workflow_params,
    )


@pytest.fixture
def integration_file_with_minimal_data(
    test_processing_params_minimal,
    test_file_1_tenant_id,
    fake_file_name,
    fake_file_path,
):
    return FileFactory.create_for_processing(
        tenant_id=test_file_1_tenant_id(),
        name=fake_file_name,
        path=fake_file_path,
        group_id=None,
        workflow_params=(test_processing_params_minimal.workflow_params),
    )


@pytest.fixture
def integration_file_max_database_limits(test_file_2_tenant_id):
    valid_name = "a" * MAX_FILE_NAME_LENGTH
    valid_path = "/" + "a" * (MAX_FILE_PATH_LENGTH - 1)

    return FileFactory.create_for_processing(
        tenant_id=test_file_2_tenant_id(),
        name=valid_name,
        path=valid_path,
        group_id=None,
        workflow_params=WorkflowParamsDict(
            document_type_id=None,
            parsing_features=[],
            needs_unifier=False,
            needs_extraction=False,
            assigned_to_me=False,
            llm_type=None,
            engine=None,
            language=None,
            metadata={},
        ),
    )


@pytest.fixture
def integration_multi_tenant_files(
    test_file_1_tenant_id,
    test_file_2_tenant_id,
    test_group_1_id,
    fake,
):
    tenant_1 = test_file_1_tenant_id()
    tenant_2 = test_file_2_tenant_id()

    name_1 = f"{fake.file_name(extension='pdf')}"
    path_1 = f"/uploads/tenant1/{name_1}"

    name_2 = f"{fake.file_name(extension='pdf')}"
    path_2 = f"/uploads/tenant2/{name_2}"

    file_1 = FileFactory.create_for_splitting(
        tenant_id=tenant_1,
        name=name_1,
        path=path_1,
        group_id=test_group_1_id(),
        classification_enabled=False,
        workflow_params=WorkflowParamsDict(
            document_type_id=str(uuid4()),
            parsing_features=[],
            needs_unifier=False,
            needs_extraction=False,
            assigned_to_me=False,
            llm_type=None,
            engine=None,
            language=None,
            metadata={},
        ),
        labels=None,
    )

    file_2 = FileFactory.create_for_classification(
        tenant_id=tenant_2,
        name=name_2,
        path=path_2,
        group_id=str(uuid4()),
        workflow_params=WorkflowParamsDict(
            document_type_id=str(uuid4()),
            parsing_features=[],
            needs_unifier=False,
            needs_extraction=False,
            assigned_to_me=False,
            llm_type=None,
            engine=None,
            language=None,
            metadata={},
        ),
        labels=None,
    )

    return file_1, file_2


@pytest.fixture
def query_file_repository(repositories):
    return repositories.query_file()


@pytest.fixture
def command_file_repository(unit_of_work):
    return unit_of_work.files


@pytest.fixture
def add_files(unit_of_work, test_files):
    for file in test_files:
        unit_of_work.files.save(file)
    unit_of_work.commit()

    yield

    unit_of_work.files.delete_all(test_files)
    unit_of_work.commit()


@pytest.fixture
def add_single_file(unit_of_work):
    def _add_file(file):
        unit_of_work.files.save(file)
        unit_of_work.commit()

    return _add_file


@pytest.fixture
def test_files(test_file_1, test_file_2):
    return [test_file_1, test_file_2]


@pytest.fixture
def add_multi_tenant_files(unit_of_work, integration_multi_tenant_files):
    file_1, file_2 = integration_multi_tenant_files
    unit_of_work.files.save(file_1)
    unit_of_work.files.save(file_2)
    unit_of_work.commit()
    return file_1, file_2


@pytest.fixture
def integration_group_with_complete_data(test_group_1_tenant_id):
    return GroupFactory.create_active(
        tenant_id=test_group_1_tenant_id(),
    )


@pytest.fixture
def integration_group_with_minimal_data(test_group_1_tenant_id, fake):
    return GroupFactory.create_active(
        tenant_id=test_group_1_tenant_id(),
    )


@pytest.fixture
def integration_groups_for_pagination(test_group_1_tenant_id):
    return [
        GroupFactory.create_for_tenant(
            tenant_id=test_group_1_tenant_id(),
        )
        for i in range(5)
    ]


@pytest.fixture
def integration_multi_tenant_groups(test_group_1_tenant_id, fake):
    tenant_2 = str(uuid4())

    group_1 = GroupFactory.create_for_tenant(
        tenant_id=test_group_1_tenant_id(),
    )

    group_2 = GroupFactory.create_for_tenant(
        tenant_id=tenant_2,
    )

    return group_1, group_2


@pytest.fixture
def add_groups(unit_of_work):
    def _add_groups(groups):
        for group in groups:
            unit_of_work.groups.save(group)
        unit_of_work.commit()

    return _add_groups


@pytest.fixture
def add_single_group(unit_of_work):
    def _add_group(group):
        unit_of_work.groups.save(group)
        unit_of_work.commit()

    return _add_group


@pytest.fixture
def command_group_repository(unit_of_work):
    return unit_of_work.groups


@pytest.fixture
def add_labels(containers):
    db = containers.datasources.postgres_session()

    def _add(file_id: str, labels: list[str]):
        if not labels:
            return
        with db.connection() as conn:
            for label in labels:
                stmt = pg_insert(label_table).values(content=label)
                stmt = stmt.on_conflict_do_nothing(index_elements=["content"])
                conn.execute(stmt)

            label_ids_query = conn.execute(label_table.select().where(label_table.c.content.in_(labels)))
            label_map = {row.content: row.label_id for row in label_ids_query}

            file_label_records = [{"file_id": file_id, "label_id": label_map[label]} for label in labels]
            conn.execute(insert(file_label_table), file_label_records)

    return _add


@pytest.fixture
def test_blob_file():
    file_content = b"Test file content"
    return BytesIO(file_content), "test_file.txt"
