FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

# Install Playwright Chromium + its system deps
RUN uv run playwright install --with-deps chromium

# Copy source code
COPY src/ src/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini .

# Install the project itself
RUN uv sync --no-dev

# Verify HTML renderer imports work (fail fast if deps are missing)
RUN uv run python -c "from legm.stats.html_renderer import generate_flexible_chart; print('html_renderer OK')"

# Create volume mount point for SQLite persistence (Railway volume mounts here)
RUN mkdir -p /data

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD pgrep -f "run_bot" || exit 1

CMD ["uv", "run", "python", "scripts/run_bot.py"]
