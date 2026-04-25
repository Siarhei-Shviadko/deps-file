from uuid import uuid4


def test_user_of_id(test_user_1_id, test_user_1, unit_of_work, add_users):
    user = unit_of_work.users.user_of_id(test_user_1_id)

    assert user == test_user_1


def test_user_of_id__user_not_found(unit_of_work, add_users):
    assert unit_of_work.users.user_of_id(uuid4().hex) is None


def test_save__user_created(test_user_1_id, test_user_1, unit_of_work):
    unit_of_work.users.save(test_user_1)

    assert unit_of_work.users.user_of_id(test_user_1_id) == test_user_1


def test_save__user_updated(test_user_1_id, test_user_1, unit_of_work, add_users):
    test_user_1.update(first_name="Mark", last_name="Jones")
    unit_of_work.users.save(test_user_1)

    assert unit_of_work.users.user_of_id(test_user_1_id) == test_user_1
