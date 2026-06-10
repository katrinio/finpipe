from sqlalchemy import func

from src.integrations.telegram.states import UserState
from src.storage.orm.system.user_state_storage import UserStateStorage


class UserStateService:
    @classmethod
    def set_state(cls, telegram_id: int, state: UserState) -> None:
        UserStateStorage.upsert(owner_telegram_id=telegram_id, state=state, updated_at=func.current_timestamp())

    @classmethod
    def get_state(cls, telegram_id: int) -> str | None:
        user_state_storage = UserStateStorage.get_by_owner(telegram_id)
        if not user_state_storage:
            return None
        return user_state_storage.state

    @classmethod
    def clear_state(cls, telegram_id: int) -> None:
        UserStateStorage.delete(telegram_id)
