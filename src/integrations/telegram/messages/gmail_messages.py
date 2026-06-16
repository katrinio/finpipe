from src.integrations.telegram.messages.common_messages import Msg


class GmailMessages:
    # TODO(vps): уточнить production-сообщения Gmail OAuth с учётом постоянного домена и поддержки пользователя.
    class Status:
        CONNECTED = Msg.success("Gmail подключён.")
        NOT_CONNECTED = "🫥 Gmail не подключён."

    class Connect:
        FAILED = Msg.error("Не удалось подключить Gmail.\nПопробуйте начать подключение заново.")
        DISCONNECTED = "📧 Gmail отключён."
        CONNECT_PROMPT = "📧 Gmail\n\nПодключите аккаунт Google для работы с банковыми письмами.\n\nНажмите кнопку ниже для авторизации."

    class Validation:
        OAUTH_TEMPORARILY_UNAVAILABLE = Msg.warning("Подключение Gmail временно недоступно.")
