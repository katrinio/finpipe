FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu libreoffice-writer postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock README.md ./


FROM base AS ci

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/* \
    && poetry install --no-root --with dev --no-interaction --no-ansi


FROM base AS production

RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY alembic.ini ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY templates ./templates

CMD ["python", "-m", "src.integrations.telegram.bot"]
