from src.integrations.telegram.messages.common_messages import MsgIcon


class InvoiceMessages:
    class Amount:
        SAVED = MsgIcon.success("Сумма Salary Invoice сохранена: {0} EUR")
        INPUT = "💰 Введите сумму Salary Invoice:"

    class Generation:
        IN_PROGRESS = MsgIcon.waiting("Формируется Salary Invoice...")
        SENT = MsgIcon.success("Salary Invoice отправлен.")
        SEND_PROMPT = "Отправить инвойс компании?"
        SEND_TO_COMPANY_SOON = "🔜 Отправка компании будет добавлена позже."

    class Validation:
        NOT_INT = MsgIcon.error("Сумма должна содержать только цифры.\nПример: 1500")
        NO_INVOICE_AMOUNT = "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму»."
        PROFILE_REQUIRED = "🏢 Профиль заполнен не полностью.\nСначала загрузите профиль и банковские реквизиты."
