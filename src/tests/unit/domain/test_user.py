from deps_file.domain.model import UserUpdated


def test_update(test_user_1):
    new_first_name = "Alicia"
    new_last_name = "Jones"

    test_user_1.update(
        first_name=new_first_name,
        last_name=new_last_name,
    )

    assert test_user_1.events
    assert test_user_1.events[-1] == UserUpdated(
        id=test_user_1.id(),
        first_name=new_first_name,
        last_name=new_last_name,
    )
