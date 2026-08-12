from dataclasses import dataclass

from deps_file.domain.model.shared import Event

__all__ = ["SplitFileExecuted"]


@dataclass(slots=True)
class SplitFileExecuted(Event):
    file_id: str
    batch_id: str | None
    error_type: str | None
    error_message: str | None
