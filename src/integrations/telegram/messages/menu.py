class MenuMessagesV2:
    MAIN_MENU = "🏠 Главное меню"

    class Sections:
        DOCUMENTS = "📄 Документы"
        SIGNATURE = "✍️ Подпись"
        GMAIL = "📧 Gmail"

    class System:
        SETTINGS = "⚙️ Настройки"
        STATUS = "ℹ️ Статус"


class MenuMessages(MenuMessagesV2):
    pass


class ConversionOrderMessagesV2:
    class Amount:
        INPUT = "💱 Укажите сумму для обмена:"
        SAVED = "✅ Сумма для обмена сохранена: {0} EUR"
        CURRENT = "💱 Сумма для обмена: {0} EUR"
        NOT_SET = "🫥 Сумма для обмена не задана."
        FROM_BANK_SAVED = "✅ Для обмена установлена сумма из банковского PDF: {0} EUR"

    class Validation:
        NOT_INT = "❌ Сумма должна содержать только цифры.\nПример: 1500"
        NO_BANK_AMOUNT = "🫥 Сумма из банковского PDF отсутствует.\nСначала обработайте банковское письмо."
        NO_CONVERSION_AMOUNT = "❌ Сумма для обмена не задана."

    class Generation:
        SENT = "✔️ Conversion Order generated!"
