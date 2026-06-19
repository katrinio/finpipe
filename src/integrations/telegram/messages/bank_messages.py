from src.integrations.telegram.messages.common_messages import MsgIcon


class BankMessages:
    class Menu:
        TITLE = "🏦 Подтверждение для банка"
        UPLOAD = "📤 Загрузите PDF для заполнения."
        CHECK = "🔎 Проверить наличие письма от банка"
        PROCESS = "📥 Найти письмо, скачать оригинал и отправить оба варианта."

    class Validation:
        SIGNATURE_REQUIRED = "✍️ Нужна подпись.\nСначала загрузите подпись в разделе «Подпись»."
        PROFILE_REQUIRED = "🏢 Профиль заполнен не полностью.\nСначала загрузите профиль и банковские реквизиты."
        NOT_PDF = "📄 Пришлите PDF-файл."
        NO_AMOUNT = "❌ Не удалось определить сумму в PDF."
        GMAIL_NOT_CONNECTED = "📧 Gmail не подключён.\nПодключите Gmail в разделе «Интеграции»."
        BANK_EMAIL_NOT_CONFIGURED = (
            "⚠️ Настройки поиска письма банка не заполнены.\n"
            "Заполните bank_confirmation_email.sender, bank_confirmation_email.recipient и bank_confirmation_email.subject_contains."
        )

    class Generation:
        IN_PROGRESS = MsgIcon.waiting("Формируется подтверждение для банка...")
        SENT = MsgIcon.success("Подтверждение для банка отправлено.")
        FILLED = MsgIcon.success("Подтверждение для банка заполнено.")
        ORIGINAL_AND_FILLED = MsgIcon.success("Письмо банка обработано и отправлено.")

    class Search:
        CHECKING = MsgIcon.waiting("Проверяю письмо из банка...")
        FOUND = MsgIcon.success("Письмо из банка найдено.")
        NOT_FOUND = MsgIcon.warning("Письмо из банка не найдено.")

    class BankDay:
        IN_PROGRESS = MsgIcon.waiting("Банковский день: ищу письмо банка...")
        EMAIL_RECEIVED = "✅ Письмо банка получено. Сумма: {} EUR"
        CONFIRMATION_READY = "✅ Подтверждение для банка готово."
        CONVERSION_READY = "✅ Запрос на конвертацию готов."
        DONE = "✅ Банковский день завершён. Сумма: {} EUR. Отправлено 3 документа."
        REPLY_PROMPT = "Отправить ответ банку на {}?\n\nБудут приложены: подтверждение, запрос на конвертацию и инвойс за прошлый период."
        REPLY_SENDING = MsgIcon.waiting("Отправляю ответ банку...")
        REPLY_SENT = MsgIcon.success("Ответ банку отправлен.")
        REPLY_SKIPPED = "Хорошо. Документы в чате."
        REPLY_NO_PENDING = "⚠️ Нет данных для ответа. Запустите банковский день заново."
