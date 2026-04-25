import json
from uuid import uuid4

import pytest
from faker import Faker
from fastapi import FastAPI
from starlette.testclient import TestClient

from deps_file.api import auth
from deps_file.domain.model import TenantId, UserFactory
from deps_file.entrypoint import create_fastapi
from deps_file.infrastructure.access_management import user
from tests.fakes import (
    FakeBatchProxy,
    FakeDocumentProxy,
    FakeDomainEventPublisher,
    FakeObjectStorageProxy,
)
from tests.shared_fixtures.file import test_file_1, test_file_2


@pytest.fixture
def fake():
    return Faker()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    fastapi_app = create_fastapi()
    yield fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def session_containers(app):
    return app.containers


@pytest.fixture
def containers(session_containers):
    with session_containers.reset_singletons():
        yield session_containers


@pytest.fixture(autouse=True)
def fake_domain_event_publisher(containers):
    with containers.domain_event_publisher.override(FakeDomainEventPublisher()) as dep:
        yield dep()


@pytest.fixture(autouse=True)
def object_storage_mock(fake_object_storage):
    yield fake_object_storage


@pytest.fixture
def repositories(containers):
    return containers.repositories


@pytest.fixture
def query_user_service(containers):
    return containers.query_user_service()


@pytest.fixture
def command_user_service(containers):
    return containers.command_user_service()


@pytest.fixture
def test_user_1_id():
    return uuid4().hex


@pytest.fixture
def test_user_1(test_user_1_id):
    user = UserFactory.make(
        id_=test_user_1_id,
        first_name="John",
        last_name="Doe",
    )
    user.events.clear()

    return user


@pytest.fixture
def test_user_2_id():
    return uuid4().hex


@pytest.fixture
def test_user_2(test_user_2_id):
    user = UserFactory.make(
        id_=test_user_2_id,
        first_name="Jane",
        last_name="Smith",
    )
    user.events.clear()

    return user


@pytest.fixture
def test_users(test_user_1, test_user_2):
    return [
        test_user_1,
        test_user_2,
    ]


@pytest.fixture
def test_files(test_file_1, test_file_2):
    return [
        test_file_1,
        test_file_2,
    ]


@pytest.fixture
def deps_token_headers_factory():
    def _make(tenant_id: str) -> dict[str, str]:
        return {
            "deps-token": json.dumps(
                {
                    "organisation": tenant_id,
                }
            )
        }

    return _make


@pytest.fixture
def deps_token_headers_default(deps_token_headers_factory):
    return deps_token_headers_factory("tenant-1")


@pytest.fixture(autouse=True)
def fake_object_storage(containers):
    with containers.external_services.object_storage.override(FakeObjectStorageProxy()) as proxy:
        yield proxy()


@pytest.fixture
def tenant_id() -> TenantId:
    return TenantId()


@pytest.fixture
def document_type_id() -> str:
    return uuid4().hex


@pytest.fixture
def this_user(tenant_id):
    return dict(
        subject="VelvetKey",
        groups=[tenant_id()],
        token="token",
        roles=["Colon"],
        organisation=tenant_id(),
    )


@pytest.fixture(autouse=True)
def set_this_user(this_user):
    user.set(this_user)


@pytest.fixture(autouse=True)
def mocked_middleware(monkeypatch, mocker):
    monkeypatch.setattr(auth, "set_user_from_token", mocker.Mock({}))


@pytest.fixture(autouse=True)
def fake_document_proxy(document_id):
    return FakeDocumentProxy(document_id)


@pytest.fixture(autouse=True)
def fake_batch_proxy(batch_id, batch_name):
    return FakeBatchProxy(batch_id=batch_id, batch_name=batch_name)
