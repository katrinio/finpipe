from src.integrations.telegram.messages.common_messages import MsgIcon


class GmailMessages:
    class Status:
        CONNECTED = MsgIcon.success("Gmail подключён.")
        NOT_CONNECTED = "🫥 Gmail не подключён."

    class Connect:
        FAILED = MsgIcon.error("Не удалось подключить Gmail.\nПопробуйте начать подключение заново.")
        DISCONNECTED = "📧 Gmail отключён."
        CONNECT_PROMPT = "📧 Gmail\n\nПодключите аккаунт Google для работы с банковыми письмами.\n\nНажмите кнопку ниже для авторизации."

    class History:
        CLEAR_PROMPT = (
            "🗑 Сбросить историю обработанных писем?\n\n"
            "Бот запоминает, какие письма от банка уже были обработаны, чтобы не обрабатывать их повторно. "
            "После сброса следующий запуск «Банковского дня» снова найдёт последнее письмо, "
            "даже если оно уже обрабатывалось.\n\n"
            "Это полезно, если нужно перепровести документы по тому же письму."
        )
        CLEARED = MsgIcon.success("История обработанных писем сброшена.")

    class Validation:
        OAUTH_TEMPORARILY_UNAVAILABLE = MsgIcon.warning("Подключение Gmail временно недоступно.")
