from src.integrations.telegram.messages.common import Msg


class OwnerMessages:
    class Access:
        INPUT_USER_ID = "Введите Telegram ID пользователя, который уже открыл бота."
        INPUT_USER_ID_TO_REVOKE = "Введите Telegram ID пользователя, у которого нужно отозвать доступ."

        USER_TO_ADD_IS_FOUND = "👤 Пользователь найден\n• {0}\n• ID: {1}\nВыдать доступ?"

        USER_TO_REVOKE_IS_FOUND = "👤 Пользователь найден\n• {0}\n• ID: {1}\nОтозвать доступ?"

        NO_ONE_WAIT_ACCESS = "Нет ожидающего подтверждения на выдачу доступа."

    class Success:
        USER_ADDED = Msg.success("Пользователь добавлен.")
        USER_REVOKED = Msg.success("Доступ пользователя отозван.")
        YOU_BEEN_ADDED = Msg.success("Администратор добавил вас в список пользователей.")

    class Info:
        EMPTY_USER_LIST = "Список пользователей пуст."
        ADD_USER_CMD = "Использование: /add_user <telegram_id>"

    class Validation:
        USER_ID_NOT_INT = "Введите корректный Telegram ID, состоящий только из цифр."
        USER_ID_NOT_KNOWN = Msg.error("Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start.")
        NO_SUCH_USER = Msg.error("У пользователя нет доступа или он не найден в списке.")
