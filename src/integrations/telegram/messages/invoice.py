from src.integrations.telegram.messages.common import Msg


class InvoiceMessages:
    class Amount:
        SAVED = Msg.success("Сумма Salary Invoice сохранена: {0} EUR")
        INPUT = "💰 Введите сумму Salary Invoice:"

    class Generation:
        IN_PROGRESS = "⏳ Формируется Salary Invoice..."
        SENT = Msg.success("Salary Invoice отправлен.")

    class Validation:
        NOT_INT = Msg.error("Сумма должна содержать только цифры.\nПример: 1500")
        NO_INVOICE_AMOUNT = "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму»."
