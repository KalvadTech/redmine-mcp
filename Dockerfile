# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.11.8 AS uv

FROM python:3.14-alpine AS builder
COPY --from=uv /uv /usr/local/bin/uv
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    rust \
    cargo \
    curl \
    wget \
    && rm -rf /var/cache/apk/*
    WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
COPY src ./src
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.14-alpine AS runtime
RUN apk add --no-cache libffi openssl \
    && addgroup -S redmine \
    && adduser -S -G redmine -u 10001 redmine
WORKDIR /app
COPY --from=builder --chown=redmine:redmine /app/.venv /app/.venv
COPY --from=builder --chown=redmine:redmine /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER redmine
EXPOSE 8765
ENTRYPOINT ["redmine-mcp"]
CMD ["--host", "0.0.0.0", "--port", "8765"]
