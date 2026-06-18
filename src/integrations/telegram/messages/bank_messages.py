from src.integrations.telegram.messages.common_messages import Msg


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
        BANK_EMAIL_NOT_CONFIGURED = (
            "⚠️ Настройки поиска письма банка не заполнены.\n"
            "Заполните bank_confirmation_email.sender, bank_confirmation_email.recipient и bank_confirmation_email.subject_contains."
        )

    class Generation:
        IN_PROGRESS = "⏳ Формируется подтверждение для банка..."
        SENT = Msg.success("Подтверждение для банка отправлено.")
        FILLED = Msg.success("Подтверждение для банка заполнено.")
        ORIGINAL_AND_FILLED = Msg.success("Письмо банка обработано и отправлено.")

    class Search:
        CHECKING = "⏳ Проверяю письмо из банка..."
        FOUND = Msg.success("Письмо из банка найдено.")
        NOT_FOUND = Msg.warning("Письмо из банка не найдено.")
