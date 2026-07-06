from src.integrations.telegram.messages.common_messages import MsgIcon


class BankMessages:
    class Validation:
        SIGNATURE_REQUIRED = "✍️ Нужна подпись.\nСначала загрузите подпись в разделе «Подпись»."
        PROFILE_REQUIRED = "🏢 Профиль заполнен не полностью.\nСначала загрузите профиль и банковские реквизиты."
        GMAIL_NOT_CONNECTED = "📧 Gmail не подключён.\nПодключите Gmail в разделе «Интеграции»."
        BANK_EMAIL_NOT_CONFIGURED = MsgIcon.warning(
            "Настройки поиска письма банка не заполнены.\n"
            "Заполните bank_confirmation_email.sender, bank_confirmation_email.recipient и bank_confirmation_email.subject_contains."
        )

    class Generation:
        IN_PROGRESS = MsgIcon.waiting("Формируется подтверждение для банка...")
        SENT = MsgIcon.success("Подтверждение для банка отправлено.")

    class Search:
        NOT_FOUND = MsgIcon.warning("Письмо из банка не найдено.")

    class BankDay:
        INFO = (
            "🏦 Банковский день\n\n"
            "Бот найдёт последнее письмо банка в Gmail и автоматически:\n"
            "• извлечёт сумму платежа\n"
            "• заполнит подтверждение для банка\n"
            "• сгенерирует инвойс за прошлый месяц\n"
            "• пришлёт оба документа\n"
            "• предложит отправить ответ банку\n\n"
            "Необходимые условия:\n"
            "{status_lines}"
        )
        IN_PROGRESS = MsgIcon.waiting("Банковский день: ищу письмо банка...")
        EMAIL_RECEIVED = MsgIcon.success("Письмо банка получено. Сумма: {} EUR")
        CONFIRMATION_READY = MsgIcon.success("Подтверждение для банка готово.")
        INVOICE_READY = MsgIcon.success("Инвойс за прошлый месяц готов.")
        DONE = MsgIcon.success("Банковский день завершён. Сумма: {} EUR. Отправлено 2 документа.")
        REPLY_PROMPT = (
            "Отправить ответ банку на {}?\n\n"
            "Будут приложены: подтверждение и инвойс за прошлый период.\n\n"
            "«Не отправлять» — письмо не уйдёт, документы будут удалены."
        )
        REPLY_SENDING = MsgIcon.waiting("Отправляю ответ банку...")
        REPLY_SENT = MsgIcon.success("Ответ банку отправлен.")
        REPLY_SKIPPED = "Хорошо. Письмо можно обработать позже через «Банковский день»."
        REPLY_NO_PENDING = MsgIcon.warning("Нет данных для ответа. Запустите банковский день заново.")

    class ConversionRequest:
        IN_PROGRESS = MsgIcon.waiting("Отправляю запрос на конвертацию...")
        SENT = MsgIcon.success("Запрос на конвертацию отправлен. Сумма: {} EUR")
        NO_AMOUNT = MsgIcon.warning("Сумма поступления не найдена.\nСначала выполните банковский день — сумма сохранится автоматически.")
        NOT_CONFIGURED = MsgIcon.warning("Адрес для запроса конвертации не заполнен.\nДобавьте conversion_request_email.to в профиль.")
