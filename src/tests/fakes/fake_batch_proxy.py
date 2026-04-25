from typing import Any
from uuid import uuid4

from deps_file.application import BatchFileDict, IBatchProxy

__all__ = ["FakeBatchProxy"]


class FakeBatchProxy(IBatchProxy):
    def __init__(self, batch_id: str | None = None, batch_name: str | None = None) -> None:
        self.batch_id = batch_id or uuid4().hex
        self.batch_name = batch_name
        self.batches: list[dict[str, Any]] = []

    def create_batch_from_files(
        self,
        batch_name: str,
        files: list[BatchFileDict],
        group_id: str | None = None,
        metadata: dict | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        parsing_features: list[str] | None = None,
    ) -> tuple[str, str]:
        result_batch_name = self.batch_name or batch_name
        self.batches.append(
            {
                "batch_name": batch_name,
                "files": files,
                "metadata": metadata,
                "group_id": group_id,
                "engine": engine,
                "language": language,
                "llm_type": llm_type,
                "parsing_features": parsing_features,
            }
        )

        return self.batch_id, result_batch_name
