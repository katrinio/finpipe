from src.integrations.telegram.messages.common_messages import Msg


class SignatureMessages:
    class Status:
        FOUND = Msg.success("Подпись загружена.")
        NOT_FOUND = Msg.warning("Подпись не найдена.")

    class Upload:
        REQUIREMENTS = "✍️ Пришлите подпись в PNG формате.\n\nТребования:\n- PNG\n- до 2 МБ\n- прозрачный фон рекомендуется"
        UPDATED = Msg.success("Подпись успешно обновлена.")

    class Validation:
        NOT_PNG = Msg.error("Разрешены только PNG файлы.")
        TOO_LARGE = Msg.error("Размер файла превышает 2 МБ")
        UPLOAD_ERROR = Msg.error("Не удалось обработать изображение.")

    class Delete:
        DELETED = "🗑️ Подпись удалена."
