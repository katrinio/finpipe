from src.integrations.telegram.messages.common_messages import MsgIcon


class InvoiceMessages:
    class Amount:
        SAVED = MsgIcon.success("Сумма Salary Invoice сохранена: {0} EUR")
        INPUT = "💰 Введите сумму Salary Invoice:"

    class Generation:
        IN_PROGRESS = MsgIcon.waiting("Формируется Salary Invoice...")
        SENT = MsgIcon.success("Salary Invoice отправлен.")

    class Validation:
        NOT_INT = MsgIcon.error("Сумма должна содержать только цифры.\nПример: 1500")
        NO_INVOICE_AMOUNT = "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму»."
