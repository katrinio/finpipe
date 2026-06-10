# Storage

<!-- TODO(HIGH):
     README ещё описывает репозитории как основной слой доступа к данным.
     После завершения миграции на Active Record нужно убрать устаревшие формулировки и сверить описание с реальными ORM-моделями. -->

`src/storage/storage.sqlite3` хранит локальное состояние проекта.

## Structure

- `database.py`
- `dependencies.py`
- `orm/`
- `repositories/`
- `storage.sqlite3`

## ORM

Все SQLAlchemy-модели живут в `src/storage/orm/`.

- `base.py` - общий `DeclarativeBase`
- `history_record.py` - история сгенерированных инвойсов
- `processed_message.py` - обработанные письма банка
- `telegram_update.py` - обработанные Telegram updates
- `user_config.py` - пользовательские настройки