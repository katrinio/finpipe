from src.integrations.telegram.messages.common_messages import MsgIcon


class InvoiceMessages:
    class Amount:
        SAVED = MsgIcon.success("Сумма инвойса сохранена: {0} EUR")
        INPUT = "💰 Введите сумму инвойса:"

    class Generation:
        IN_PROGRESS = MsgIcon.waiting("Формируется инвойс...")
        SENT = MsgIcon.success("Инвойс отправлен.")
        SEND_PROMPT = "Отправить инвойс компании на {}?"
        SENDING = MsgIcon.waiting("Отправляю инвойс компании...")
        SENT_TO_COMPANY = MsgIcon.success("Инвойс отправлен компании.")

    class Validation:
        NOT_INT = MsgIcon.error("Сумма должна содержать только цифры.\nПример: 1500")
        NO_INVOICE_AMOUNT = "💰 Сумма инвойса не задана.\nИспользуйте «Указать сумму»."
        PROFILE_REQUIRED = "🏢 Профиль заполнен не полностью.\nСначала загрузите профиль и банковские реквизиты."
