from uuid import uuid4

import pytest

from deps_file.domain.model import Group, GroupId
from deps_file.domain.model.shared import TenantId
from tests.factories import GroupFactory

__all__ = [
    "test_group_1_id",
    "test_group_1_tenant_id",
    "test_group_2_id",
    "test_group_2_tenant_id",
    "test_group_1",
    "test_group_2",
    "test_group_minimal",
    "test_group_for_deletion",
    "test_groups_different_tenants",
    "save_group",
]


@pytest.fixture
def test_group_1_id() -> GroupId:
    return GroupId()


@pytest.fixture
def test_group_1_tenant_id() -> TenantId:
    return TenantId()


@pytest.fixture
def test_group_2_id() -> GroupId:
    return GroupId()


@pytest.fixture
def test_group_2_tenant_id() -> TenantId:
    return TenantId()


@pytest.fixture
def test_group_1(test_group_1_id, tenant_id) -> Group:
    return Group(
        id_=test_group_1_id(),
        tenant_id=tenant_id(),
        is_deleted=False,
    )


@pytest.fixture
def test_group_2(test_group_2_id, test_group_2_tenant_id) -> Group:
    return Group(
        id_=test_group_2_id(),
        tenant_id=test_group_2_tenant_id(),
        is_deleted=False,
    )


@pytest.fixture
def test_group_minimal() -> Group:
    return GroupFactory.create_active()


@pytest.fixture
def test_group_for_deletion() -> Group:
    return GroupFactory.create_active()


@pytest.fixture
def test_groups_different_tenants() -> list[Group]:
    tenant_1 = str(uuid4())
    tenant_2 = str(uuid4())

    group_1 = Group(
        id_=None,
        tenant_id=tenant_1,
    )

    group_2 = Group(
        id_=None,
        tenant_id=tenant_2,
    )

    return [group_1, group_2]


@pytest.fixture
def save_group(fake_unit_of_work_with_groups, test_group_1) -> None:
    fake_unit_of_work_with_groups.groups.save(test_group_1)
