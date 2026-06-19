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

    class Search:
        NOT_FOUND = MsgIcon.warning("Письмо из банка не найдено.")

    class BankDay:
        INFO = (
            "🏦 <b>Банковский день</b>\n\n"
            "Бот найдёт последнее письмо банка в Gmail и автоматически:\n"
            "• извлечёт сумму платежа\n"
            "• заполнит Bank Confirmation\n"
            "• сгенерирует Conversion Order\n"
            "• сгенерирует инвойс за прошлый месяц\n"
            "• пришлёт все три документа\n"
            "• предложит отправить ответ банку\n\n"
            "Необходимые условия:\n"
            "{status_lines}"
        )
        IN_PROGRESS = MsgIcon.waiting("Банковский день: ищу письмо банка...")
        EMAIL_RECEIVED = MsgIcon.success("Письмо банка получено. Сумма: {} EUR")
        CONFIRMATION_READY = MsgIcon.success("Подтверждение для банка готово.")
        CONVERSION_READY = MsgIcon.success("Запрос на конвертацию готов.")
        INVOICE_READY = MsgIcon.success("Инвойс за прошлый месяц готов.")
        DONE = MsgIcon.success("Банковский день завершён. Сумма: {} EUR. Отправлено 3 документа.")
        REPLY_PROMPT = (
            "Отправить ответ банку на {}?\n\n"
            "Будут приложены: подтверждение, запрос на конвертацию и инвойс за прошлый период.\n\n"
            "«Не отправлять» — письмо не уйдёт, документы будут удалены."
        )
        REPLY_SENDING = MsgIcon.waiting("Отправляю ответ банку...")
        REPLY_SENT = MsgIcon.success("Ответ банку отправлен.")
        REPLY_SKIPPED = "Хорошо. Письмо можно обработать позже через «Банковский день»."
        REPLY_NO_PENDING = MsgIcon.warning("Нет данных для ответа. Запустите банковский день заново.")
