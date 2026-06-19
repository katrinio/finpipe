# ⚙️ Workflows

Workflows — высокоуровневые пользовательские сценарии, объединяющие несколько tasks в один законченный процесс.

---

## 🔄 Workflows

### `generate_invoice_and_send`

Подготовка Salary Invoice и отправка в Telegram с последующим выбором — отправить письмо компании или нет.

| Шаг | Действие |
|---|---|
| 1 | Генерация Salary Invoice за текущий период |
| 2 | Создание PDF и DOCX |
| 3 | Сохранение попытки в `document_generation_history` |
| 4 | Отправка PDF в Telegram |
| 5 | Удаление DOCX; PDF остаётся до решения пользователя |
| 6a | «Отправить компании»: `send_invoice_email` → письмо → удаление PDF |
| 6b | «Не сейчас»: `discard_invoice_pdf` → удаление PDF |

**Env для тестирования отправки письма:**

| Переменная | Назначение |
|---|---|
| `EMAIL_DRY_RUN` | `true` — письмо не отправляется, только логируется |
| `EMAIL_DRY_RUN_RECIPIENT` | Подменяет адрес получателя (актуально при `false`) |

---

### `process_bank_request`

Основной банковский сценарий.

| Шаг | Действие |
|---|---|
| 1 | Поиск нового банковского письма (текущий месяц) |
| 2 | Загрузка PDF-вложения |
| 3 | Извлечение данных из письма |
| 4 | Генерация Bank Confirmation с подписью |
| 5 | Отправка результата в Telegram |

---

### `daily_monitoring_summary`

Ежедневная сводка по реальным production-данным.

```
GitHub Actions (cron: 05:00 UTC)
       │  SSH
       ▼
      VPS: docker compose exec finpipe-bot
                  │
                  ▼
       src/workflows/monitoring/daily_report
                  │  читает app_events за 24ч
                  ▼
         Telegram monitoring chat
```

**Secrets GitHub Actions:**

| Secret | Назначение |
|---|---|
| `VPS_HOST` | Адрес VPS |
| `VPS_USER` | SSH-пользователь |
| `VPS_PORT` | SSH-порт |
| `VPS_SSH_KEY` | Приватный ключ |

> ⚠️ `cron` работает в UTC. `05:00 UTC` = `07:00` по Белграду (без учёта DST).

---

### `check_bank_email`

Мониторинг входящего письма банка о зачислении. Запускается по cron с 2 по 6 число каждого месяца.

| Шаг | Действие |
|---|---|
| 1 | Проверяет что сегодня 2–6 число месяца |
| 2 | Итерирует всех `AllowedUser` |
| 3 | Для каждого: ищет новое письмо через `find_bank_email(telegram_id)` |
| 4 | Если найдено и уведомление ещё не отправлялось — пишет пользователю в Telegram |
| 5 | Сохраняет маркер `notify:{telegram_id}:{message_id}` в `ProcessedMessage` |

- Не скачивает вложения, не помечает письмо как обработанное
- Повторный запуск безопасен — дубль не отправится
- Маркер сбрасывается вместе с «🗑 Сбросить историю писем»
- При отсутствии Gmail у пользователя — молча пропускает, продолжает для других

---

### `backup_database`

Резервное копирование production PostgreSQL.

| Шаг | Действие |
|---|---|
| 1 | Читает настройки: `BACKUP_DIR`, `BACKUP_RETENTION_DAYS` |
| 2 | Создаёт папку `backups`, если нет |
| 3 | Запускает `pg_dump` внутри postgres-контейнера |
| 4 | Сжимает в gzip |
| 5 | Проверяет что архив создан и не пустой |
| 6 | Удаляет бэкапы старше `BACKUP_RETENTION_DAYS` |
| 7 | Отправляет статус в monitoring chat |

**Ключевые env:**

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | Строка подключения |
| `BACKUP_DIR` | Папка для бэкапов |
| `BACKUP_RETENTION_DAYS` | Срок хранения |
| `BACKUP_POSTGRES_SERVICE` | Имя postgres-сервиса в compose |
| `MONITORING_CHAT_ID` | Куда слать статус |

---

## 🔩 Tasks

Tasks — низкоуровневые операции, используемые внутри workflows и при отладке.

| Task | Назначение |
|---|---|
| `generate_invoice` | Генерация Salary Invoice (PDF + DOCX, история в БД) |
| `generate_conversion_order` | Генерация Conversion Order с подписью |
| `generate_bank_confirmation` | Генерация Bank Confirmation с подписью |
| `fetch_bank_email` | Поиск письма банка + загрузка вложений |
| `clear_processed_history` | Сброс истории обработанных писем |
