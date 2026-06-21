from src.integrations.telegram.messages.common_messages import MsgIcon


class ProfileMessages:
    class Upload:
        REQUIREMENTS = (
            "✍️ Пришлите заполненный шаблон в YAML формате.\n\nТребования:\n- YAML\n- до 2 МБ\n- заполнен словарем значений по ключам шаблона"
        )
        TEMPLATE_SENT = "📥 Шаблон профиля отправлен.\nЗаполните файл и загрузите его обратно."
        UPDATED = MsgIcon.success("Данные пользователя успешно обновлены.")

    class Validation:
        NOT_YAML = MsgIcon.error("Разрешены только YAML файлы.")
        TOO_LARGE = MsgIcon.error("Размер файла превышает 2 МБ.")
