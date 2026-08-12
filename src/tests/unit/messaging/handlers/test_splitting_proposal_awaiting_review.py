import pytest

from deps_file.domain.model.file import Status
from deps_file.messaging.handlers import splitting_proposal_awaiting_review_handler


@pytest.mark.usefixtures("save_test_file_for_splitting", "save_group")
def test_splitting_proposal_awaiting_review_handler__sets_splitting_review_status(
    splitting_proposal_awaiting_review_envelope,
    # command_file_service,
    fake_command_file_repository,
    tenant_id,
):
    splitting_proposal_awaiting_review_handler(splitting_proposal_awaiting_review_envelope)

    file = fake_command_file_repository.file_of_id(
        splitting_proposal_awaiting_review_envelope.event.proposal_id,
        tenant_id(),
    )
    assert file.status == Status.SPLITTING_REVIEW
