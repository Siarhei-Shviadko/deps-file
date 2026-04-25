import pytest

from deps_file.domain.model.file import (
    FileFiltering,
    FileSortBy,
    FileSorting,
    FileSortOrder,
)
from deps_file.domain.model.shared import Pagination
from deps_file.infrastructure.repositories.file.query_factory import QueryFileFactory
from tests.helpers.sqlalchemy import compile_sql_with_literals


def test_filtered_file_ids_builds_filters_sorting_and_pagination():
    factory = QueryFileFactory()

    filtering = FileFiltering(
        tenant_id="tenant-1",
        name="Doc",
        state=["PROCESSING"],
        labels=["alpha", "beta"],
        date_start=None,
        date_end=None,
    )
    sorting = FileSorting(sort_by=FileSortBy.NAME, sort_order=FileSortOrder.ASC)
    pagination = Pagination(page=2, per_page=5)

    query = factory.filtered_file_ids(filtering=filtering, sorting=sorting, pagination=pagination)

    sql = compile_sql_with_literals(query)

    assert "tenant-1" in sql
    # SQLAlchemy escapes percent signs when compiling with literal_binds
    assert "ILIKE '%%Doc%%'" in sql
    assert "PROCESSING" in sql
    assert "alpha" in sql and "beta" in sql
    assert "ORDER BY" in sql and "name" in sql and "ASC" in sql
    assert "LIMIT 5" in sql and "OFFSET 5" in sql


@pytest.mark.parametrize(
    "sorting,expect",
    [
        (
            FileSorting(sort_by=FileSortBy.CREATED_AT, sort_order=FileSortOrder.DESC),
            "DESC",
        ),
        (
            FileSorting(sort_by=FileSortBy.STATE, sort_order=FileSortOrder.DESC),
            "DESC",
        ),
        (
            FileSorting(sort_by=FileSortBy.NAME, sort_order=FileSortOrder.ASC),
            "ASC",
        ),
    ],
)
def test_find_all_with_applies_ordering_after_join(sorting, expect):
    factory = QueryFileFactory()

    filtering = FileFiltering(tenant_id="t")
    pagination = Pagination(page=1, per_page=10)

    ids_cte = factory.filtered_file_ids(filtering=filtering, sorting=sorting, pagination=pagination)
    query = factory.find_all_with(ids_cte, sorting=sorting)
    sql = compile_sql_with_literals(query)

    assert "SELECT" in sql and "FROM" in sql and "JOIN" in sql
    assert "ORDER BY" in sql and expect in sql


def test_filters_name_only():
    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        name="Doc",
        state=None,
        labels=None,
        date_start=None,
        date_end=None,
    )
    sorting = FileSorting()
    pagination = Pagination(page=1, per_page=10)

    query = factory.filtered_file_ids(filtering, sorting, pagination)
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "ILIKE '%%Doc%%'" in sql


def test_filters_single_state():
    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        name=None,
        state=["PROCESSING"],
        labels=None,
        date_start=None,
        date_end=None,
    )
    query = factory.filtered_file_ids(filtering, FileSorting(), Pagination(page=1, per_page=10))
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "(file.state ->> 'status') IN ('PROCESSING')" in sql


def test_filters_multi_state_uses_in():
    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        name=None,
        state=["COMPLETED", "FAILED"],
        labels=None,
        date_start=None,
        date_end=None,
    )
    query = factory.filtered_file_ids(filtering, FileSorting(), Pagination(page=1, per_page=10))
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "(file.state ->> 'status') IN ('COMPLETED', 'FAILED')" in sql


def test_filters_date_range():
    from datetime import datetime

    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        name=None,
        state=None,
        labels=None,
        date_start=datetime(2024, 1, 1, 0, 0, 0),
        date_end=datetime(2024, 12, 31, 23, 59, 59),
    )
    query = factory.filtered_file_ids(filtering, FileSorting(), Pagination(page=1, per_page=10))
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "file.created_at >=" in sql
    assert "file.created_at <=" in sql
    assert "2024-01-01" in sql
    assert "2024-12-31" in sql


def test_filters_single_label():
    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        labels=["alpha"],
        name=None,
        state=None,
        date_start=None,
        date_end=None,
    )
    query = factory.filtered_file_ids(filtering, FileSorting(), Pagination(page=1, per_page=10))
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "label.content ILIKE '%%alpha%%'" in sql


def test_filters_multi_label_uses_or():
    factory = QueryFileFactory()
    filtering = FileFiltering(
        tenant_id="tenant-1",
        labels=["alpha", "beta"],
        name=None,
        state=None,
        date_start=None,
        date_end=None,
    )
    query = factory.filtered_file_ids(filtering, FileSorting(), Pagination(page=1, per_page=10))
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-1'" in sql
    assert "label.content ILIKE '%%alpha%%'" in sql
    assert "label.content ILIKE '%%beta%%'" in sql
    assert " OR " in sql


@pytest.mark.parametrize(
    "case",
    [
        {
            "filtering": dict(name="Doc", state=None, labels=None, date_start=None, date_end=None),
            "sorting": dict(sort_by=FileSortBy.NAME, sort_order=FileSortOrder.ASC),
            "pagination": dict(page=2, per_page=5),
            "expects": [
                "ILIKE '%%Doc%%'",
                "ORDER BY",
                "name",
                "ASC",
                "LIMIT 5",
                "OFFSET 5",
            ],
        },
        {
            "filtering": dict(
                name=None,
                state=["PROCESSING"],
                labels=["alpha", "beta"],
                date_start=None,
                date_end=None,
            ),
            "sorting": dict(sort_by=FileSortBy.CREATED_AT, sort_order=FileSortOrder.DESC),
            "pagination": dict(page=1, per_page=10),
            "expects": [
                "(file.state ->> 'status') IN ('PROCESSING')",
                "alpha",
                "beta",
                "ORDER BY",
                "DESC",
            ],
        },
        {
            "filtering": dict(
                name=None,
                state=["COMPLETED", "FAILED"],
                labels=["alpha"],
                date_start=None,
                date_end=None,
            ),
            "sorting": dict(sort_by=FileSortBy.CREATED_AT, sort_order=FileSortOrder.DESC),
            "pagination": dict(page=1, per_page=10),
            "expects": [
                "(file.state ->> 'status') IN ('COMPLETED', 'FAILED')",
                "alpha",
                "ORDER BY",
                "DESC",
            ],
        },
        {
            "filtering": dict(
                name=None,
                state=None,
                labels=["alpha"],
                date_start="2024-01-01T00:00:00",
                date_end="2024-12-31T23:59:59",
            ),
            "sorting": dict(sort_by=FileSortBy.STATE, sort_order=FileSortOrder.DESC),
            "pagination": dict(page=3, per_page=1),
            "expects": [
                "file.created_at >=",
                "file.created_at <=",
                "2024-01-01",
                "2024-12-31",
                "alpha",
                "ORDER BY",
                "DESC",
                "LIMIT 1",
                "OFFSET 2",
            ],
        },
    ],
)
def test_filtered_file_ids_parametrized(case):
    from datetime import datetime

    factory = QueryFileFactory()

    date_start = case["filtering"]["date_start"]
    date_end = case["filtering"]["date_end"]
    if isinstance(date_start, str):
        date_start = datetime.fromisoformat(date_start)
    if isinstance(date_end, str):
        date_end = datetime.fromisoformat(date_end)

    filtering = FileFiltering(
        tenant_id="tenant-x",
        name=case["filtering"]["name"],
        state=case["filtering"]["state"],
        labels=case["filtering"]["labels"],
        date_start=date_start,
        date_end=date_end,
    )
    sorting = FileSorting(
        sort_by=case["sorting"]["sort_by"],
        sort_order=case["sorting"]["sort_order"],
    )
    pagination = Pagination(
        page=case["pagination"]["page"],
        per_page=case["pagination"]["per_page"],
    )

    query = factory.filtered_file_ids(filtering, sorting, pagination)
    sql = compile_sql_with_literals(query)

    assert "file.tenant_id = 'tenant-x'" in sql
    for expected in case["expects"]:
        assert expected in sql
