import pytest

from deps_file.domain.model import FileDeleted, ICommandFileRepository
from deps_file.messaging.handlers import delete_file_handler
from tests.fakes import FakeDomainEventPublisher


@pytest.mark.usefixtures("save_file")
def test_delete_file_handler(
    delete_file_command_message,
    test_file_1_id,
    file_path,
    fake_command_file_repository: ICommandFileRepository,
    fake_domain_event_publisher: FakeDomainEventPublisher,
    tenant_id,
):
    delete_file_handler(delete_file_command_message)

    assert not fake_command_file_repository.file_of_id(id_=test_file_1_id(), tenant_id=tenant_id())
    [event] = fake_domain_event_publisher.last_published.events
    assert isinstance(event, FileDeleted)
    assert event.id == test_file_1_id()
    assert event.path == file_path
