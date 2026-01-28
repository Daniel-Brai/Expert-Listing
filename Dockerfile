FROM python:3.14-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    gcc \
    build-essential \
    gettext \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

RUN uv venv .venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/
ENV PYTHONUNBUFFERED=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY ./app/uv.lock ./app/pyproject.toml ./

# Install dependencies using uv (without installing the project itself)
RUN uv sync --frozen --no-install-project

COPY ./app/ ./

# Copy local env file to .env inside the container
COPY .env.docker .env

# Run the application using uv
CMD ["uv", "run", "python", "main.py"]

