from sqlalchemy.dialects import postgresql


def compile_sql_with_literals(selectable) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)
