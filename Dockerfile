FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH=/app/.venv/bin:$PATH \
    FLASK_APP=app.run

WORKDIR /app

# Dependencies
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY app ./app

ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

RUN useradd --system --no-create-home app
USER app

CMD ["sh", "-c", "exec gunicorn --workers 2 --bind :${PORT:-8080} --log-file - app.run:app"]
