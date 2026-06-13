from src.integrations.telegram.messages.common import Msg


class ProfileMessageV2:
    class Status:
        FOUND = Msg.success("Подпись загружена.")
        NOT_FOUND = Msg.warning("Подпись не найдена.")

    class Upload:
        REQUIREMENTS = (
            "✍️ Пришлите заполненный шаблон в YAML формате.\n\nТребования:\n- YAML\n- до 2 МБ\n- заполнен словарем значений по ключам шаблона"
        )
        TEMPLATE_SENT = "📥 Шаблон профиля отправлен.\nЗаполните файл и загрузите его обратно."
        UPDATED = Msg.success("Данные пользователя успешно обновлены.")
        UPLOADED = Msg.success("Профиль успешно загружен.\nКомпания: {0}\nБанк: {1}")

    class Validation:
        NOT_YAML = Msg.error("Разрешены только YAML файлы.")
        TOO_LARGE = Msg.error("Размер файла превышает 2 МБ.")


class ProfileMessages(ProfileMessageV2):
    pass
