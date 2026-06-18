from src.integrations.telegram.messages.common_messages import MsgIcon


class SignatureMessages:
    class Status:
        FOUND = MsgIcon.success("Подпись загружена.")
        NOT_FOUND = MsgIcon.warning("Подпись не найдена.")

    class Upload:
        REQUIREMENTS = "✍️ Пришлите подпись в PNG формате.\n\nТребования:\n- PNG\n- до 2 МБ\n- прозрачный фон рекомендуется"
        UPDATED = MsgIcon.success("Подпись успешно обновлена.")

    class Validation:
        NOT_PNG = MsgIcon.error("Разрешены только PNG файлы.")
        TOO_LARGE = MsgIcon.error("Размер файла превышает 2 МБ")
        UPLOAD_ERROR = MsgIcon.error("Не удалось обработать изображение.")

    class Delete:
        DELETED = "🗑️ Подпись удалена."
