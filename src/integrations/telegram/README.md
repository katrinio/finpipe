# Telegram architecture

## Architecture

```text
Telegram Update
↓
TelegramBot
↓
CommandRouter
↓
Domain Handler
↓
Service
↓
Storage
```

## File responsibilities

- `bot.py` - принимает Telegram updates, проверяет доступ, маршрутизирует upload-состояния и делегирует команды `CommandRouter`.
- `commands.py` - константы кнопок и команд, а также форматирование пользовательских сообщений.
- `states.py` - enum пользовательских состояний для upload-flow.
- `state_service.py` - хранение и чтение состояния пользователя.
- `handlers/command_router.py` - маршрутизация команд Telegram на доменные handlers.
- `handlers/system_handlers.py` - команды системы: status, healthcheck, about, whoami, last action.
- `handlers/gmail_handlers.py` - команды Gmail: connect, disconnect, status.
- `handlers/signature_handlers.py` - upload/delete/status для подписи.
- `handlers/profile_handlers.py` - upload/download шаблона профиля.
- `handlers/menu_handlers.py` - показ меню и навигация.
- `handlers/state_handlers.py` - описание обработчиков upload-состояний.

## How to add a new command

1. Добавить текст команды или кнопку в `commands.py` или `ui/buttons.py`.
2. Реализовать метод в подходящем domain handler.
3. Зарегистрировать команду в `CommandRouter._build_command_handlers()`.
4. Добавить тест на поведение команды.

## How to add a new upload-flow

1. Добавить новое значение в `UserState`.
2. Зарегистрировать `StateHandler` в `TelegramBot._state_handlers`.
3. Реализовать метод обработки файла в нужном handler.
4. Добавить команду, которая переводит пользователя в нужное состояние.
5. Добавить unit-тест на set state, success path и invalid file path.

## Структура меню
```aiignore
Главное меню
├── Gmail
│   ├── Статус
│   ├── Подключить
│   └── Отключить
│
├── Подпись
│   ├── Статус
│   ├── Загрузить
│   └── Удалить
│
├── Настройки
│   ├── Скачать шаблон
│   └── Загрузить шаблон
│
└── Система
    ├── Статус
    ├── Healthcheck
    ├── About
    └── Last action
```