from typing import cast

from src.integrations.telegram.states import UserState
from src.storage.orm.system.user_state_storage import UserStateStorage


class UserStateService:
    """Сервис хранения пользовательских состояний."""

    _memory_states: dict[int, UserState] = {}

    @staticmethod
    def _uses_database() -> bool:
        return hasattr(UserStateStorage, "database")

    @staticmethod
    def set_state(telegram_id: int, state: UserState) -> None:
        if not UserStateService._uses_database():
            UserStateService._memory_states[telegram_id] = state
            return

        UserStateStorage.upsert(owner_telegram_id=telegram_id, state=state)

    @staticmethod
    def get_state(telegram_id: int) -> UserState | None:
        if not UserStateService._uses_database():
            return UserStateService._memory_states.get(telegram_id)

        user_state_storage = UserStateStorage.get_by_owner(telegram_id)
        if not user_state_storage:
            return None
        return cast(UserState, user_state_storage.state)

    @staticmethod
    def clear_state(telegram_id: int) -> None:
        if not UserStateService._uses_database():
            UserStateService._memory_states.pop(telegram_id, None)
            return

        UserStateStorage.delete(telegram_id)
