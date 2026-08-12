from dataclasses import dataclass

from deps_file.domain.model.shared import Event

__all__ = ["SplittingProposalAwaitingReview"]


@dataclass(slots=True)
class SplittingProposalAwaitingReview(Event):
    proposal_id: str
