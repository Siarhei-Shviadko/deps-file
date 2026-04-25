import pytest

from deps_file.domain.model.file import (
    FileFiltering,
    FileSortBy,
    FileSorting,
    FileSortOrder,
)
from deps_file.domain.model.shared import Pagination
from tests.helpers.seeders import seed_files_with_dates


@pytest.mark.parametrize(
    "name",
    [None, "doc"],
)
@pytest.mark.parametrize("state", [None, ["PROCESSING"], ["COMPLETED", "FAILED"]])
@pytest.mark.parametrize(
    "labels",
    [None, ["alpha"], ["alpha", "beta"]],
)
@pytest.mark.parametrize(
    "sort_by,sort_order",
    [
        (FileSortBy.CREATED_AT, FileSortOrder.DESC),
        (FileSortBy.NAME, FileSortOrder.ASC),
    ],
)
@pytest.mark.parametrize("page,per_page", [(1, 1), (2, 1)])
def test_find_all_with_params(
    query_file_repository,
    unit_of_work,
    test_file_1_tenant_id,
    add_labels,
    name,
    state,
    labels,
    sort_by,
    sort_order,
    page,
    per_page,
):
    tenant_id = test_file_1_tenant_id()
    files = seed_files_with_dates(unit_of_work, tenant_id)

    add_labels(files[0].id(), ["alpha"])  # matches alpha/alp
    add_labels(files[1].id(), ["beta"])  # matches beta

    filtering = FileFiltering(
        tenant_id=tenant_id,
        name=name,
        state=state,
        labels=labels,
        date_start=None,
        date_end=None,
    )
    sorting = FileSorting(sort_by=sort_by, sort_order=sort_order)
    pagination = Pagination(page=page, per_page=per_page)

    result = query_file_repository.find_all_with(
        filtering=filtering,
        sorting=sorting,
        pagination=pagination,
    )

    assert "files" in result and "result_set" in result
    files_result = result["files"]
    rs = result["result_set"]

    assert rs["count"] == len(files_result)
    assert rs["limit"] >= len(files_result)

    if labels is None and state is None:
        assert rs["total"] == len(files)
    else:
        assert rs["total"] >= len(files_result)

    if labels:
        has_labels = any(fi.get("labels") for fi in files_result)
        assert has_labels or len(files_result) == 0
