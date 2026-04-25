from typing import Any

from deps_file.domain.model import Reference, ReferenceType

__all__ = ["ReferenceMapper"]


class ReferenceMapper:
    @staticmethod
    def to_dict(reference: Reference) -> dict[str, Any]:
        return {
            "entity_type": reference.entity_type.value,
            "entity_id": reference.entity_id,
            "entity_name": reference.entity_name,
        }

    @staticmethod
    def from_dict(reference_dict: dict[str, Any]) -> Reference:
        return Reference(
            entity_type=ReferenceType(reference_dict["entity_type"]),
            entity_id=reference_dict["entity_id"],
            entity_name=reference_dict["entity_name"],
        )
