from sqlalchemy import Boolean, Column, String, Table

from deps_file.extras import metadata

__all__ = ["group_table"]


group_table = Table(
    "group",
    metadata,
    Column("group_id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("is_deleted", Boolean, nullable=False),
)
