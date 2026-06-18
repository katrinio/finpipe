FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice \
        fonts-dejavu \
        curl \
        git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --with dev