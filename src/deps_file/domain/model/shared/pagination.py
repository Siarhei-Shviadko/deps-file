from dataclasses import dataclass

__all__ = ["Pagination"]


@dataclass
class Pagination:
    page: int
    per_page: int

    @property
    def limit(self) -> int:
        return self.per_page

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def first_element_index(self) -> int:
        return self.offset

    @property
    def last_element_index(self) -> int:
        return self.first_element_index + self.per_page
