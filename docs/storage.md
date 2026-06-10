# Storage

## Где хранится база

SQLite база приложения хранится в `data/finpipe.db`.

Каталог `data/` создаётся автоматически при старте приложения, ручная подготовка не нужна.

## Какие данные сохраняются

- `UserConfig`
- `CompanyProfile`
- `BankDetails`
- `GmailAccount`
- `Signature`
- `UserStateStorage`
- `OAuthSession`
- `AuditLog`
- `AllowedUser`
- `HistoryRecord`
- `ProcessedMessage`
- `TelegramUpdate`

## Что переживает рестарт приложения

- профили пользователей
- банковские реквизиты
- Gmail-аккаунты
- подписи
- состояния upload-flow
- OAuth sessions
- аудит действий
- разрешённые Telegram-пользователи
- обработанные сообщения и updates

## Что не сохраняется

- временные объекты в памяти процесса;
- текущие in-memory состояния, если приложение запускается без доступной SQLite БД.

## Backup

Самый простой способ создать резервную копию:

```bash
cp data/finpipe.db backup.db
```

## Recovery

Восстановление из копии:

```bash
cp backup.db data/finpipe.db
```

После восстановления достаточно перезапустить приложение.
