FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for skia-python (used by pictex for chart rendering)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libegl1 libgl1 libgles2 libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini .

# Install the project itself
RUN uv sync --no-dev

# Verify pictex/skia imports work (fail fast if system deps are missing)
RUN uv run python -c "from pictex import Canvas; print('pictex OK')"

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD pgrep -f "run_bot" || exit 1

CMD ["uv", "run", "python", "scripts/run_bot.py"]
