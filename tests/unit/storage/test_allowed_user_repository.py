from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.allowed_user_repository import SQLAlchemyAllowedUserRepository


def test_allowed_user_repository_add_get_and_list_all(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    repository = SQLAlchemyAllowedUserRepository(database.session)

    assert repository.get_by_telegram_id(249517409) is None
    assert repository.list_all() == []

    repository.add(telegram_id=249517409, user_name="erichismyonlyfamily")
    repository.add(telegram_id=249517409, user_name="erichismyonlyfamily")

    user = repository.get_by_telegram_id(249517409)

    assert user is not None
    assert user.telegram_id == 249517409
    assert user.user_name == "erichismyonlyfamily"
    assert [item.telegram_id for item in repository.list_all()] == [249517409]
