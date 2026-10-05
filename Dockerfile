FROM node:24-bookworm-slim AS harness-builder

WORKDIR /opt/deepseek-harness

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential git python3 \
    && rm -rf /var/lib/apt/lists/* \
    && corepack enable

COPY --from=harness . ./
RUN pnpm install --frozen-lockfile \
    && pnpm run build:lib:host \
    && rm -rf .git

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    DSH_HOME=/data/dsh \
    DSH_WORKSPACE=/app \
    PYTHONPATH=/app/src:/opt/deepseek-harness/python/sdk/src

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates libstdc++6 \
    && pip install --no-cache-dir poetry==2.2.1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN poetry install --only main --no-root

COPY --from=harness-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=harness-builder /opt/deepseek-harness /opt/deepseek-harness
COPY src/ ./src/
COPY docker/dsh /usr/local/bin/dsh
RUN chmod +x /usr/local/bin/dsh

CMD ["python", "-m", "main"]
