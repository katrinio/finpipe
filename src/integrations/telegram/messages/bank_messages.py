from src.integrations.telegram.messages.common_messages import MsgIcon


class BankMessages:
    class Confirmation:
        UPLOAD = "🏦 Пришлите исходный банковский документ в PDF формате."
        IN_PROGRESS = MsgIcon.waiting("Формируется подтверждение банковского перевода...")
        SENT = MsgIcon.success("Подтверждение банковского перевода отправлено.")

    class ConversionRequest:
        IN_PROGRESS = MsgIcon.waiting("Формируется запрос на конвертацию...")
        SENT = MsgIcon.success("Запрос на конвертацию отправлен.")

    class Validation:
        PROFILE_REQUIRED = "🏢 Профиль заполнен не полностью.\nСначала загрузите профиль и банковские реквизиты."
        SIGNATURE_REQUIRED = "✍️ Нужна подпись.\nСначала загрузите подпись в разделе «Профиль»."
        NO_BANK_AMOUNT = "💶 Сумма поступления не найдена.\nСначала сформируйте подтверждение банковского перевода."
        NOT_PDF = MsgIcon.error("Исходный банковский документ должен быть PDF-файлом.")
        TOO_LARGE = MsgIcon.error("Исходный банковский документ слишком большой.")
        INVALID_PDF = MsgIcon.error("Не удалось прочитать исходный банковский PDF.")
        GENERATION_FAILED = MsgIcon.error("Не удалось сформировать документ.")
