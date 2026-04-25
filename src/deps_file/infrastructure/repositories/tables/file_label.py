from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)

from deps_file.constants import UUID_FIELD_LENGTH
from deps_file.extras import metadata

__all__ = ["file_label_table"]


file_label_table = Table(
    "file_label",
    metadata,
    Column(
        "file_id",
        String(UUID_FIELD_LENGTH),
        ForeignKey("file.file_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "label_id",
        Integer,
        ForeignKey("label.label_id"),
        primary_key=True,
        nullable=False,
    ),
    UniqueConstraint("file_id", "label_id", name="uk_file_label_file_id_label_id"),
)
