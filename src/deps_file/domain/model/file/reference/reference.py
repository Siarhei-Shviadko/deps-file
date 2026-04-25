from deps_file.domain.model.shared import Guard, ImmutableCheck

from .reference_type import ReferenceType

__all__ = ["Reference"]


class Reference:
    entity_type = Guard[ReferenceType](ReferenceType, ImmutableCheck())
    entity_id = Guard[str](str, ImmutableCheck())
    entity_name = Guard[str](str, ImmutableCheck())

    def __init__(
        self,
        entity_type: ReferenceType,
        entity_id: str,
        entity_name: str,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_name = entity_name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and other.entity_type == self.entity_type
            and other.entity_id == self.entity_id
            and other.entity_name == self.entity_name
        )

    def __repr__(self) -> str:
        return " ".join(
            (
                f"entity_type={self.entity_type},",
                f"entity_id={self.entity_id},",
                f"entity_name={self.entity_name},",
            ),
        )
