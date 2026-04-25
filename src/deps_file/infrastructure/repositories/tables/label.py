from sqlalchemy import Column, Integer, String, Table

from deps_file.constants import MAX_LABEL_CONTENT_LENGTH
from deps_file.extras import metadata

__all__ = ["label_table"]


label_table = Table(
    "label",
    metadata,
    Column("label_id", Integer, primary_key=True, autoincrement=True),
    Column(
        "content",
        String(MAX_LABEL_CONTENT_LENGTH),
        nullable=False,
        unique=True,
    ),
)
