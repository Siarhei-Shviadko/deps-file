from uuid import uuid4


def test_find_user(test_user_1_id, test_user_1, query_user_repository, add_users):
    user = query_user_repository.find_user(test_user_1_id)

    assert user == {
        "id": test_user_1_id,
        "first_name": test_user_1.first_name,
        "last_name": test_user_1.last_name,
    }


def test_find_user__user_not_found(query_user_repository, add_users):
    assert query_user_repository.find_user(uuid4().hex) is None
