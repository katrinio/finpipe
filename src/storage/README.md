# Storage

`data/finpipe.db` хранит локальное состояние проекта между запусками.

Подробное описание хранения данных и восстановления находится в [docs/storage.md](../docs/storage.md).

## Structure

- `database.py`
- `dependencies.py`
- `orm/`

## ORM

Все SQLAlchemy-модели живут в `src/storage/orm/`.

- `base.py` - общий `DeclarativeBase`
- `history_record.py` - история сгенерированных инвойсов
- `processed_message.py` - обработанные письма банка
- `telegram_update.py` - обработанные Telegram updates
- `user_config.py` - пользовательские настройки
