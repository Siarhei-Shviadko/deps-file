from functools import cached_property
from types import MappingProxyType as ImmutableDict
from typing import Any, Callable, Collection, Tuple

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import Join, Select, distinct, select

from deps_file.constants import (
    CTE_FILE_ID_COLUMN,
    CTE_FILES_TO_SELECT,
    LABELS_AGGREGATE_COLUMN,
)
from deps_file.domain.exceptions import IllegalArgument
from deps_file.domain.model.file import (
    FileFiltering,
    FileSortBy,
    FileSorting,
    FileSortOrder,
)
from deps_file.domain.model.shared import Pagination

from ..tables import file_label_table, file_reference_table, file_table, label_table

__all__ = ["QueryFileFactory"]


class QueryFileFactory:  # noqa: WPS214
    SORTING_FIELD_MAP: ImmutableDict[FileSortBy, Tuple[sa.Column, ...]] = ImmutableDict(
        {
            FileSortBy.NAME: (file_table.c.name,),
            FileSortBy.STATE: (file_table.c.state["status"], file_table.c.created_at),
            FileSortBy.CREATED_AT: (file_table.c.created_at,),
        },
    )

    SORTING_ORDER_MAP: ImmutableDict[FileSortOrder, Callable] = ImmutableDict(
        {
            FileSortOrder.ASC: sa.asc,
            FileSortOrder.DESC: sa.desc,
        },
    )

    @cached_property
    def file_columns(self) -> Tuple[sa.Column, ...]:
        return (  # noqa: WPS227
            file_table.c.file_id,
            file_table.c.tenant_id,
            file_table.c.name,
            file_table.c.path,
            file_table.c.state,
            file_table.c.processing_params,
            file_table.c.created_at,
            file_table.c.updated_at,
        )

    def find_file(self, file_id: str, tenant_id: str) -> Select:
        return self.base_select_query().where(
            sa.and_(
                file_table.c.file_id == file_id,
                file_table.c.tenant_id == tenant_id,
            ),
        )

    def find_files_by_ids(self, file_ids: set[str], tenant_id: str) -> Select:
        return self.base_select_query().where(
            sa.and_(
                file_table.c.file_id.in_(file_ids),
                file_table.c.tenant_id == tenant_id,
            ),
        )

    def save_file(self, file_dict: dict[str, Any]) -> sa.Insert:
        return insert(file_table).on_conflict_do_update(index_elements=["file_id"], set_=file_dict)

    def save_labels(self) -> sa.Insert:
        return (
            insert(label_table)
            .on_conflict_do_update(index_elements=["content"], set_={"content": label_table.c.content})
            .returning(label_table.c.label_id)
        )

    def save_labels_to_file(self) -> sa.Insert:
        return insert(file_label_table).on_conflict_do_nothing()

    def save_reference(self) -> sa.Insert:
        return insert(file_reference_table).on_conflict_do_update(
            index_elements=["file_id"],
            set_={
                "entity_type": file_reference_table.c.entity_type,
                "entity_id": file_reference_table.c.entity_id,
                "entity_name": file_reference_table.c.entity_name,
            },
        )

    def delete_files(self, file_ids: Collection[str], tenant_id: str) -> tuple:
        file_label_del = sa.delete(file_label_table).where(file_label_table.c.file_id.in_(file_ids))
        orphan_label_del = sa.delete(label_table).where(
            ~label_table.c.label_id.in_(select(file_label_table.c.label_id)),
        )
        file_del = sa.delete(file_table).where(
            sa.and_(file_table.c.file_id.in_(file_ids), file_table.c.tenant_id == tenant_id),
        )
        return file_label_del, orphan_label_del, file_del

    def filtered_file_ids(self, filtering: FileFiltering, sorting: FileSorting, pagination: Pagination) -> Select:
        query = self.base_cte_query()
        query = self._apply_filters(query, filtering)
        query = self._apply_sorting(query, sorting)

        query_with_total = query.add_columns(sa.func.count().over().label("total_count"))

        return self._apply_pagination(query_with_total, pagination)

    def find_all_with(self, cte_query: Select, sorting: FileSorting) -> Select:
        cte_query = cte_query.cte(CTE_FILES_TO_SELECT)

        query = self.base_select_query().join(
            cte_query,
            file_table.c.file_id == getattr(cte_query.c, CTE_FILE_ID_COLUMN),
        )
        return self._apply_sorting(query, sorting)

    def find_all_with_count(self, cte_query: Select, sorting: FileSorting) -> Select:
        cte_query = cte_query.cte(CTE_FILES_TO_SELECT)

        query = (
            self.base_select_query()
            .add_columns(sa.func.max(cte_query.c.total_count).label("total_count"))
            .join(
                cte_query,
                file_table.c.file_id == getattr(cte_query.c, CTE_FILE_ID_COLUMN),
            )
        )
        return self._apply_sorting(query, sorting)

    @cached_property
    def joined_file_labels_references(self) -> Join:
        file_to_junction = sa.outerjoin(
            file_table,
            file_label_table,
            file_table.c.file_id == file_label_table.c.file_id,
        )

        file_to_labels = sa.outerjoin(
            file_to_junction,
            label_table,
            file_label_table.c.label_id == label_table.c.label_id,
        )

        return sa.outerjoin(
            file_to_labels,
            file_reference_table,
            file_table.c.file_id == file_reference_table.c.file_id,
        )

    def base_select_query(self) -> Select:
        reference_object = sa.case(  # noqa: WPS317
            (
                sa.func.max(file_reference_table.c.entity_type).is_not(None),
                sa.func.json_build_object(
                    "entity_type",
                    sa.func.max(file_reference_table.c.entity_type),
                    "entity_id",
                    sa.func.max(file_reference_table.c.entity_id),
                    "entity_name",
                    sa.func.max(file_reference_table.c.entity_name),
                ),
            ),
            else_=None,
        )

        return (
            select(
                *self.file_columns,
                sa.func.array_remove(sa.func.array_agg(label_table.c.content), None).label(LABELS_AGGREGATE_COLUMN),
                reference_object.label("reference"),
            )
            .select_from(self.joined_file_labels_references)
            .group_by(*self.file_columns)
        )

    def base_cte_query(self) -> Select:
        return (
            select(file_table.c.file_id.label(CTE_FILE_ID_COLUMN))
            .select_from(
                self.joined_file_labels_references,
            )
            .group_by(file_table.c.file_id)
        )

    def _apply_filters(self, query: Select, filtering: FileFiltering) -> Select:
        query = query.where(file_table.c.tenant_id == filtering.tenant_id)

        if filtering.name:
            query = query.where(file_table.c.name.ilike(f"%{filtering.name}%"))

        if filtering.state:
            query = query.where(file_table.c.state["status"].astext.in_(filtering.state))

        if filtering.date_start:
            query = query.where(file_table.c.created_at >= filtering.date_start)

        if filtering.date_end:
            query = query.where(file_table.c.created_at <= filtering.date_end)

        if filtering.labels:
            label_conditions = [label_table.c.content.ilike(f"%{label}%") for label in filtering.labels]
            query = query.where(sa.or_(*label_conditions))

        if filtering.reference_available is True:
            query = query.where(file_reference_table.c.file_id.isnot(None))

        if filtering.entity_name:
            query = query.where(file_reference_table.c.entity_name.ilike(f"%{filtering.entity_name}%"))

        return query

    def _apply_pagination(self, query: Select, pagination: Pagination) -> Select:
        return query.offset(pagination.offset).limit(pagination.limit)

    def _apply_sorting(self, query: Select, sorting: FileSorting) -> Select:
        if not sorting:
            return query.order_by(file_table.c.created_at.desc())

        if sorting.sort_by not in self.SORTING_FIELD_MAP:
            supported_fields = list(self.SORTING_FIELD_MAP.keys())
            raise IllegalArgument(f"Unsupported sort field: {sorting.sort_by}. Supported fields: {supported_fields}")

        sort_columns = self.SORTING_FIELD_MAP[sorting.sort_by]
        sort_order_func = self.SORTING_ORDER_MAP.get(sorting.sort_order, sa.desc)

        sort_expressions = [sort_order_func(column).nulls_last() for column in sort_columns]

        # Required for DISTINCT compatibility when using multiple sort columns
        for index, column in enumerate(sort_columns):
            query = query.add_columns(column.label(f"sort_column_{index}"))

        return query.order_by(*sort_expressions)

    def _needs_cte_pattern_for_filters(self, filtering: FileFiltering) -> bool:
        return bool(filtering.labels and len(filtering.labels) > 1)
