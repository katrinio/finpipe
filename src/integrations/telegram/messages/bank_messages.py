from src.integrations.telegram.messages.common_messages import Msg


class BankMessages:
    class Validation:
        SIGNATURE_REQUIRED = "✍️ Нужна подпись.\nСначала загрузите подпись в разделе «Подпись»."

    class Generation:
        IN_PROGRESS = "⏳ Формируется подтверждение для банка..."
        SENT = Msg.success("Подтверждение для банка отправлено.")
