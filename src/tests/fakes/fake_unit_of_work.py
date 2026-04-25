from deps_file.infrastructure.unit_of_work import AbstractUnitOfWork

__all__ = ["FakeUnitOfWork"]


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        users=None,
        files=None,
        groups=None,
        file_references=None,
    ) -> None:
        self.users = users
        self.files = files
        self.groups = groups
        self.file_references = file_references
        self._in_transaction_calls = 0
        self._commit_calls = 0
        self._rollback_calls = 0

    def __enter__(self) -> AbstractUnitOfWork:
        self._in_transaction_calls += 1
        return self

    def commit(self):
        self._commit_calls += 1

    def rollback(self):
        self._rollback_calls += 1
