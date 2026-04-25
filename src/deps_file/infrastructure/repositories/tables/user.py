from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB

from deps_file.extras import metadata

__all__ = ["user_table"]


user_table = Table(
    "user",
    metadata,
    Column("user_id", String, primary_key=True),
    Column("first_name", String, nullable=False),
    Column("last_name", String, nullable=False),
)
