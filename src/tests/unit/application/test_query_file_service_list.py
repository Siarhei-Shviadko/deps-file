from datetime import datetime, timezone

import pytest

from deps_file.domain.model.file import (
    FileFiltering,
    FileSortBy,
    FileSorting,
    FileSortOrder,
)
from deps_file.domain.model.shared import Pagination


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(
            name=None,
            state=None,
            labels=None,
            date_start=None,
            date_end=None,
            reference_available=None,
            entity_name=None,
            page=1,
            per_page=20,
            sort_by=FileSortBy.CREATED_AT,
            sort_order=FileSortOrder.DESC,
        ),
        dict(
            name="q",
            state=["FAILED"],
            labels=["lab"],
            date_start=None,
            date_end=None,
            reference_available=True,
            entity_name="Invoice",
            page=3,
            per_page=5,
            sort_by=FileSortBy.NAME,
            sort_order=FileSortOrder.ASC,
        ),
        dict(
            name=None,
            state=["COMPLETED"],
            labels=["alpha", "beta"],
            date_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            date_end=datetime(2024, 12, 31, tzinfo=timezone.utc),
            reference_available=False,
            entity_name=None,
            page=2,
            per_page=10,
            sort_by=FileSortBy.STATE,
            sort_order=FileSortOrder.DESC,
        ),
        dict(
            name=None,
            state=["COMPLETED", "FAILED"],
            labels=None,
            date_start=None,
            date_end=None,
            reference_available=None,
            entity_name=None,
            page=1,
            per_page=20,
            sort_by=FileSortBy.CREATED_AT,
            sort_order=FileSortOrder.DESC,
        ),
    ],
)
def test_service_forwards_filters_to_repo(query_file_repository, query_file_service, mocker, kwargs):
    mock_find_all_with = mocker.patch.object(query_file_repository, "find_all_with")

    query_file_service.find_all_with(
        tenant_id="tenant-1",
        **kwargs,
    )

    assert mock_find_all_with.call_count == 1
    call_kwargs = mock_find_all_with.call_args.kwargs

    filtering = call_kwargs["filtering"]
    sorting = call_kwargs["sorting"]
    pagination = call_kwargs["pagination"]

    assert isinstance(filtering, FileFiltering)
    assert filtering.tenant_id == "tenant-1"
    assert filtering.name == kwargs["name"]
    assert filtering.state == kwargs["state"]
    assert filtering.labels == kwargs["labels"]
    assert filtering.date_start == kwargs["date_start"]
    assert filtering.date_end == kwargs["date_end"]
    assert filtering.reference_available == kwargs["reference_available"]
    assert filtering.entity_name == kwargs["entity_name"]

    assert isinstance(sorting, FileSorting)
    assert sorting.sort_by == kwargs["sort_by"]
    assert sorting.sort_order == kwargs["sort_order"]

    assert isinstance(pagination, Pagination)
    assert pagination.page == kwargs["page"]
    assert pagination.per_page == kwargs["per_page"]
