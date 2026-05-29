# FINPIPE 🚧 In progress! 🚧
Automates invoice generation and accounting workflows based on bank emails.

## Настройка локального окружения

### Виртуальное окружение:
1. Выполнить команду ```python -m venv .venv``` - создание виртуального окружения
2. Выполнить команду ```. .venv/bin/activate``` - активация виртуального окружения

### Установка зависимостей:
1. Выполнить команду ```pip install poetry==2.2.1``` - установка пакета poetry, который управляет зависимостями
2. Выполнить команды для установки зависимостей ```poetry install --no-interaction --no-ansi --no-cache```

### Pre-commit:

1. Установить pre-commit, если он еще не установлен ```poetry add --group dev pre-commit```
2. Установить git hook ```poetry run pre-commit install```

### Генерация инвойса:
1. Выполнить команду:
```bash
poetry run generate-invoice --amount 1000
```

2. Готовые файлы сохраняются в папку ```output/invoice```:

### Обработка банковского письма:
1. Заполнить в ```.env``` переменные ```GMAIL_CREDENTIALS_PATH```, ```GMAIL_TOKEN_PATH```, ```BANK_EMAIL_SUBJECT``` и ```BANK_EMAIL_FROM```.

2. Выполнить команду:
```bash
poetry run process_bank_email
```
