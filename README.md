# finpipe
Pet project for accounting workflow automation.

# Настройка локального окружения

### Репозиторий (или просто создать Project From Version Control):
1. Выполнить команду ```git init``` - создает новый репозиторий Git или преобразует существующий каталог в репозиторий Git

### Виртуальное окружение:
1. Выполнить команду ```python -m venv .venv``` - создание виртуального окружения
2. Выполнить команду ```. .venv/bin/activate``` - активация виртуального окружения

### Установка зависимостей:
1. Выполнить команду ```pip install poetry==2.2.1``` - установка пакета poetry, который управляет зависимостями
2. Выполнить команды для установки зависимостей ```poetry install --no-interaction --no-ansi --no-cache```

### Генерация инвойса:
1. Выполнить команду:
```bash
poetry run generate-invoice --amount 1000
```

2. Готовые файлы сохраняются в папку ```output/invoices```:
```text
output/invoices/invoice-YYYY-MM.docx
output/invoices/invoice-YYYY-MM.pdf
```

### Pre-commit:
Pre-commit запускается только локально при коммите после установки git hook.

1. Установить pre-commit, если он еще не установлен:
```bash
poetry add --group dev pre-commit
```

2. Установить git hook:
```bash
poetry run pre-commit install
```

3. Проверить весь проект вручную:
```bash
poetry run pre-commit run --all-files
```

Если pre-commit автоматически исправил файлы, нужно добавить эти изменения в git и повторить commit.
