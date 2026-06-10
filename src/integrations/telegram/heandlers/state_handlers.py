from collections.abc import Callable
from dataclasses import dataclass

from src.integrations.telegram.states import UserState


@dataclass(frozen=True)
class StateHandler:
    """Обработчик состояния ожидания файла."""

    handler: Callable[[int, str, int, bytes], None]
    error_message: str


def _process_waiting_state(
    self,
    telegram_id: int,
    update: dict,
) -> bool:
    """Обрабатывает состояния ожидания загрузки файла."""

    state_handlers = {
        UserState.WAITING_SIGNATURE_UPLOAD: StateHandler(
            handler=self.handlers._handle_signature_upload,
            error_message="✍️ Пришлите подпись в PNG формате.",
        ),
        UserState.WAITING_PROFILE_TEMPLATE_UPLOAD: StateHandler(
            handler=self.handlers._handle_profile_template_upload,
            error_message="📄 Пришлите заполненный шаблон в YAML формате.",
        ),
    }

    state = self.handlers.get_user_state(telegram_id)
    state_handler = state_handlers.get(state)

    if state_handler is None:
        return False

    file_data = self.extract_document_upload_data(update)

    if file_data is None:
        self.telegram.send_message(state_handler.error_message)
        self.update_storage.mark_processed(update["update_id"])
        return True

    file_name, file_size, file_id, _ = file_data

    file_path = self.telegram.get_file(file_id)
    file_bytes = self.telegram.download_file(file_path)

    state_handler.handler(
        telegram_id,
        file_name,
        file_size,
        file_bytes,
    )

    self.update_storage.mark_processed(update["update_id"])
    return True
