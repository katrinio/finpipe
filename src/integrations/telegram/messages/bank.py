from src.integrations.telegram.messages.common import Msg


class BankMessagesV2:
    class Generation:
        IN_PROGRESS = "⏳ Формируется подтверждение для банка..."
        SENT = Msg.success("Подтверждение для банка отправлено.")


class ConversionOrderMessages:
    NO_EXCHANGE_AMOUNT = "❌ Сумма к обмену не определена.\nСначала обработайте банковский PDF, чтобы сохранить полученную сумму."


class BankMessages(BankMessagesV2):
    pass
