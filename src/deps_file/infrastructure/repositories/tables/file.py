from sqlalchemy import Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import JSONB

from deps_file.constants import (
    MAX_FILE_PATH_LENGTH,
    MAX_TABLE_NAME_LENGTH,
    UUID_FIELD_LENGTH,
)
from deps_file.extras import metadata

__all__ = ["file_table"]


file_table = Table(
    "file",
    metadata,
    Column("file_id", String(UUID_FIELD_LENGTH), primary_key=True),
    Column("tenant_id", String(UUID_FIELD_LENGTH), nullable=False),
    Column("name", String(MAX_TABLE_NAME_LENGTH), nullable=False),
    Column("path", String(MAX_FILE_PATH_LENGTH), nullable=False),
    Column("state", JSONB, nullable=False),
    Column("processing_params", JSONB, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)
