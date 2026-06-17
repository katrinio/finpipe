# Workflows

Workflows — высокоуровневые пользовательские сценарии.

Обычно workflow объединяет несколько задач (tasks) в один законченный процесс.

Права доступа и onboarding пользователей происходят через Telegram workflow, а не через отдельные CLI-команды.

Примеры:

- сформировать и отправить Salary Invoice;
- обработать банковское письмо;
- выполнить ежедневную проверку системы.

---

## generate_invoice_and_send

Основной сценарий подготовки Salary Invoice.

Workflow:

1. Генерирует Salary Invoice за текущий период.
2. Создаёт PDF и DOCX версии документа.
3. Сохраняет результат попытки генерации в историю БД.
4. Отправляет результат в Telegram.
5. Удаляет временные файлы после отправки.

---

## process_bank_request

Основной банковский сценарий.

Workflow:

1. Проверяет новые банковские письма.
2. Загружает PDF-вложения.
3. Извлекает данные из письма.
4. Заполняет банковские документы.
5. Отправляет результат в Telegram.

---

## daily_monitoring_summary

Ежедневная сводка мониторинга по реальным данным production.

Workflow:

1. GitHub Actions срабатывает по расписанию и выступает только как таймер.
2. По SSH подключается к VPS.
3. На VPS переходит в `~/projects/finpipe`.
4. Запускает `docker compose exec -T -w /app finpipe-bot poetry run python -m src.workflows.monitoring.daily_report`.
5. Скрипт читает `app_events` из production PostgreSQL за последние 24 часа.
6. Формирует короткий Telegram-отчёт и отправляет его в monitoring chat.

Причина запуска на VPS:

- отчёт должен строиться по реальным production-данным;
- в CI нет доступа к prod PostgreSQL;
- рядом с приложением уже доступны prod env, docker compose и нужные секреты.

Secrets для GitHub Actions:

- `VPS_HOST`
- `VPS_USER`
- `VPS_PORT`
- `VPS_SSH_KEY`

Расписание:

- `cron` в GitHub Actions работает в UTC;
- для 07:00 по Белграду используется фиксированное значение `05:00 UTC` как MVP;
- при смене DST cron нужно пересматривать.

---

# Tasks

Tasks — низкоуровневые операции, которые могут использоваться как внутри workflows, так и отдельно во время разработки, тестирования или отладки.

---

## generate_invoice

Генерирует Salary Invoice из шаблонов.

- Формирует данные за период.
- Создаёт PDF и DOCX документы.
- Сохраняет в БД историю каждой попытки генерации.
- Использует `DocumentType.SALARY_INVOICE` и `DocumentGenerationStatus`.
- Не блокирует повторную генерацию по уже использованному `document_number`.

---

## generate_conversion_order

Генерирует Conversion Order.

- Заполняет шаблон документа.
- Создаёт PDF.
- При наличии подписи добавляет её в документ.
- Сохраняет историю генерации в `document_generation_history` c типом `conversion_order`.

---

## generate_bank_confirmation

Генерирует Bank Confirmation.

- Подставляет реквизиты пользователя.
- Подставляет сумму и дату.
- При наличии подписи добавляет её в документ.
- Сохраняет историю генерации в `document_generation_history` c типом `bank_confirmation`.

---

## fetch_bank_email

Получает банковские письма.

- Находит новое письмо банка.
- Загружает вложения.
- Помечает письмо как обработанное.

---

## clear_processed_history

Очищает историю обработанных банковских писем.

Используется для повторной обработки писем и локальной отладки.
