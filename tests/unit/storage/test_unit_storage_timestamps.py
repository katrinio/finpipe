from datetime import UTC, datetime
from pathlib import Path

from src.integrations.telegram.states import UserState
from src.storage.orm import Signature, UserConfig
from src.storage.orm.database import Database
from src.storage.orm.system.user_state_storage import UserStateStorage
from tests.helpers.database import initialize_test_database


def test_updated_timestamps_are_stored_without_microseconds(tmp_path: Path) -> None:
    database = Database.from_env()
    initialize_test_database(database)

    now = datetime.now(UTC).replace(tzinfo=None)
    UserConfig.upsert(telegram_id=10, invoice_amount_eur=1000)
    UserConfig.upsert(telegram_id=10, invoice_amount_eur=1500)
    user_config = UserConfig.get_by_owner(10)
    assert user_config is not None
    assert abs((now - user_config.created_at).total_seconds()) < 5
    assert abs((now - user_config.updated_at).total_seconds()) < 5

    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_INVOICE_AMOUNT)
    UserStateStorage.upsert(owner_telegram_id=11, state=UserState.WAITING_PROFILE_TEMPLATE_UPLOAD)
    user_state = UserStateStorage.get_by_owner(11)
    assert user_state is not None
    assert abs((now - user_state.created_at).total_seconds()) < 5
    assert user_state.updated_at is not None
    assert abs((now - user_state.updated_at).total_seconds()) < 5

    signature_path = tmp_path / "signature.enc"
    signature_path.write_text("signature")
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    Signature.create(owner_telegram_id=12, signature_path=signature_path)
    signature = Signature.get_by_owner(12)
    assert signature is not None
    assert abs((now - signature.created_at).total_seconds()) < 5
    assert abs((now - signature.updated_at).total_seconds()) < 5
