import abc

from deps_file.domain.model import ICommandUserRepository
from deps_file.domain.model.file import ICommandFileRepository
from deps_file.domain.model.group import ICommandGroupRepository

__all__ = ["AbstractUnitOfWork"]


class AbstractUnitOfWork(abc.ABC):
    users: ICommandUserRepository
    files: ICommandFileRepository
    groups: ICommandGroupRepository

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError
