from deps_object_storage import FileAlreadyExists, FileNotFound, ObjectStorage

__all__ = ["FakeObjectStorageProxy"]


class FakeObjectStorageProxy(ObjectStorage):
    def __init__(self) -> None:
        self._storage: dict[str, bytes] = {}

    def upload(self, path: str, content: bytes, replace_if_exists: bool) -> str:
        if not replace_if_exists and path in self._storage:
            raise FileAlreadyExists(path)
        self._storage[path] = content
        return path

    def download(self, path: str) -> bytes:
        if path in self._storage:
            return self._storage[path]

        raise FileNotFound(path)

    def delete(self, path: str) -> None:
        if path in self._storage:
            del self._storage[path]
        else:
            raise FileNotFound(path)
