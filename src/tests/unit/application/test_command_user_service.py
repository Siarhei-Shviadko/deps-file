from uuid import uuid4

import pytest

from deps_file.domain.exceptions import UserNotFound


def test_find_user(test_user_1_id, test_user_1, command_user_service):
    user = command_user_service.find_user(test_user_1_id)

    assert user == test_user_1


def test_find_user__user_not_found(command_user_service):
    with pytest.raises(UserNotFound):
        command_user_service.find_user(uuid4().hex)


def test_save_user__user_created(command_user_service, fake):
    command_user_service.save_user(id_=uuid4().hex, first_name=fake.first_name(), last_name=fake.last_name())


def test_save_user__user_updated(command_user_service, test_user_1_id, fake):
    command_user_service.save_user(id_=test_user_1_id, first_name=fake.first_name(), last_name=fake.last_name())
