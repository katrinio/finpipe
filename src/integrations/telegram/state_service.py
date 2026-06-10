from typing import cast

from src.integrations.telegram.states import UserState
from src.storage.orm.system.user_state_storage import UserStateStorage


class UserStateService:
    """Сервис хранения пользовательских состояний."""

    @staticmethod
    def set_state(telegram_id: int, state: UserState) -> None:
        UserStateStorage.upsert(owner_telegram_id=telegram_id, state=state)

    @staticmethod
    def get_state(telegram_id: int) -> UserState | None:
        user_state_storage = UserStateStorage.get_by_owner(telegram_id)
        if not user_state_storage:
            return None
        return cast(UserState, user_state_storage.state)

    @staticmethod
    def clear_state(telegram_id: int) -> None:
        UserStateStorage.delete(telegram_id)
