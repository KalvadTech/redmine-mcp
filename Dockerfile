FROM python:3.14-alpine

RUN apk add --no-cache build-base libffi-dev openssl-dev rust cargo curl wget \
    && pip install --no-cache-dir uv==0.11.8 \
    && addgroup -S redmine \
    && adduser -S -G redmine -u 10001 redmine

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock LICENSE README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

USER redmine
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/up || exit 1
ENTRYPOINT ["redmine-mcp"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
