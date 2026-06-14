FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

COPY alembic.ini README.md ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY templates ./templates
COPY attachments ./attachments

CMD ["start_bot"]
