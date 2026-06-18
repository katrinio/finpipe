from src.integrations.telegram.messages.common_messages import MsgIcon


class GmailMessages:
    # TODO(vps): уточнить production-сообщения Gmail OAuth с учётом постоянного домена и поддержки пользователя.
    class Status:
        CONNECTED = MsgIcon.success("Gmail подключён.")
        NOT_CONNECTED = "🫥 Gmail не подключён."

    class Connect:
        FAILED = MsgIcon.error("Не удалось подключить Gmail.\nПопробуйте начать подключение заново.")
        DISCONNECTED = "📧 Gmail отключён."
        CONNECT_PROMPT = "📧 Gmail\n\nПодключите аккаунт Google для работы с банковыми письмами.\n\nНажмите кнопку ниже для авторизации."

    class Validation:
        OAUTH_TEMPORARILY_UNAVAILABLE = MsgIcon.warning("Подключение Gmail временно недоступно.")
