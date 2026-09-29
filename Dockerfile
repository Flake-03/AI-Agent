FROM node:24-bookworm-slim AS harness-builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential git python3 \
    && rm -rf /var/lib/apt/lists/* \
    && corepack enable

WORKDIR /opt/deepseek-harness
COPY --from=harness . ./
RUN pnpm install --frozen-lockfile \
    && pnpm run build:lib:host

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    AGENT_HOST=0.0.0.0 \
    AGENT_PORT=8080

WORKDIR /app
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates libstdc++6 \
    && pip install --no-cache-dir poetry==2.2.1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=harness-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=harness-builder /opt/deepseek-harness /opt/deepseek-harness
COPY pyproject.toml ./
RUN poetry install --only main --no-root
COPY src/ ./src/
COPY docker/dsh /usr/local/bin/dsh
RUN useradd --create-home --uid 10001 appuser \
    && chmod 0555 /usr/local/bin/dsh \
    && mkdir -p /data/dsh/documenter /data/dsh/knowledge \
    && chown -R appuser:appuser /data

ENV PYTHONPATH=/app/src:/opt/deepseek-harness/python/sdk/src

USER appuser
CMD ["python", "-m", "main"]
