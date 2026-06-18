# 🗄️ Storage

Storage отвечает за долговременное хранение данных Finpipe.

Все пользовательские настройки, профили, состояния Telegram, Gmail-аккаунты и системные данные хранятся в PostgreSQL и переживают перезапуск приложения.

Подробная схема хранения: [docs/storage.md](../../docs/storage.md)

---

## 📁 Структура

```
storage/
├── orm/                         ORM-модели
│   ├── user/                    Пользовательские данные
│   │   ├── allowed_user.py
│   │   ├── known_user.py
│   │   ├── company_profile.py
│   │   ├── bank_details.py
│   │   ├── user_config.py
│   │   ├── signature.py
│   │   └── gmail_account.py
│   └── system/                  Системные данные
│       ├── audit_log.py
│       ├── user_state_storage.py
│       ├── telegram_update.py
│       ├── processed_message.py
│       ├── oauth_session.py
│       ├── document_generation_history.py
│       └── app_events.py
├── dependencies.py              Сборка зависимостей
└── bootstrap_allowed_users.py  Первичная инициализация owner
```

---

## 👤 Пользовательские модели

| Модель | Таблица | Назначение |
|---|---|---|
| `AllowedUser` | `allowed_user` | Авторизованные пользователи + роли |
| `KnownUser` | `known_user` | Пользователи, открывавшие бота |
| `CompanyProfile` | `company_profile` | Данные работодателя |
| `BankDetails` | `bank_details` | Банковские реквизиты |
| `UserConfig` | `user_config` | Настройки (суммы Invoice и конвертации) |
| `Signature` | `signature` | Подпись: метаданные + зашифрованные байты |
| `GmailAccount` | `gmail_account` | Gmail: refresh token (зашифрован), email, ошибка |

---

## ⚙️ Системные модели

| Модель | Таблица | Назначение |
|---|---|---|
| `AuditLog` | `audit_log` | Журнал всех команд и OAuth-событий |
| `UserStateStorage` | `user_state_storage` | Текущее состояние Telegram workflow |
| `TelegramUpdate` | `telegram_update` | Обработанные updates (защита от дублей) |
| `ProcessedMessage` | `processed_message` | Обработанные банковские письма |
| `OAuthSession` | `oauth_sessions` | Временные сессии Gmail OAuth |
| `DocumentGenerationHistory` | `document_generation_history` | История попыток генерации |
| `AppEvent` | `app_events` | Системные события для мониторинга |

---

## 🔒 Безопасность

| Данные | Защита |
|---|---|
| Gmail refresh token | Зашифрован через `TokenCipher` |
| Подпись пользователя | Зашифрована через `SignatureCipher` |
| Чувствительные поля | Не должны попадать в логи |

---

## 🛠️ Добавить новую ORM-модель

1. Добавить файл в `src/storage/orm/user/` или `src/storage/orm/system/`
2. Экспортировать через `__init__.py`
3. Создать Alembic-миграцию: `poetry run alembic revision --autogenerate -m "description"`
4. Добавить тесты
5. Обновить [docs/storage.md](../../docs/storage.md)
