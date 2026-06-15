FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

RUN apt-get update \
    && apt-get install -y libreoffice \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

COPY alembic.ini README.md ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY templates ./templates

CMD ["python", "-m", "src.integrations.telegram.bot"]