from abc import ABC, abstractmethod

from .batch_file_dict import BatchFileDict

__all__ = ["IBatchProxy"]


class IBatchProxy(ABC):
    @abstractmethod
    def create_batch_from_files(
        self,
        batch_name: str,
        files: list[BatchFileDict],
        source_file_id: str,
        group_id: str | None = None,
        metadata: dict | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        parsing_features: list[str] | None = None,
    ) -> tuple[str, str]:
        pass
