from sqlalchemy import Column, ForeignKey, Index, String, Table

from deps_file.constants import (
    MAX_TABLE_NAME_LENGTH,
    MAX_TABLE_TYPE_LENGTH,
    UUID_FIELD_LENGTH,
)
from deps_file.extras import metadata

__all__ = ["file_reference_table"]


file_reference_table = Table(
    "file_reference",
    metadata,
    Column(
        "file_id",
        String(UUID_FIELD_LENGTH),
        ForeignKey("file.file_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column("entity_type", String(MAX_TABLE_TYPE_LENGTH), nullable=False),
    Column("entity_id", String(UUID_FIELD_LENGTH), nullable=False),
    Column("entity_name", String(MAX_TABLE_NAME_LENGTH), nullable=False),
    Index("idx_file_reference_entity_id", "entity_id"),
)
